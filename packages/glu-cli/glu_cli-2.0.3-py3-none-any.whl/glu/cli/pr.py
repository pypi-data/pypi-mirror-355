import re
from typing import Annotated

import rich
import typer
from git import Commit, InvalidGitRepositoryError
from InquirerPy import inquirer
from jira import JIRAError

from glu.ai import (
    generate_description,
    get_ai_client,
    prompt_for_chat_provider,
)
from glu.config import (
    JIRA_IN_PROGRESS_TRANSITION,
    JIRA_READY_FOR_REVIEW_TRANSITION,
)
from glu.gh import get_github_client, prompt_for_reviewers
from glu.jira import (
    format_jira_ticket,
    generate_ticket_with_ai,
    get_jira_client,
    get_jira_project,
    get_user_from_jira,
)
from glu.local import (
    checkout_to_branch,
    generate_commit_with_ai,
    get_git_client,
)
from glu.utils import (
    print_error,
)

app = typer.Typer()


@app.command(short_help="Create a PR with description")
def create(  # noqa: C901
    ticket: Annotated[
        str | None,
        typer.Option("--ticket", "-t", help="Jira ticket number"),
    ] = None,
    project: Annotated[
        str | None,
        typer.Option("--project", "-p", help="Jira project (defaults to default Jira project)"),
    ] = None,
    draft: Annotated[bool, typer.Option("--draft", "-d", help="Mark as draft PR")] = False,
    reviewers: Annotated[
        list[str] | None,
        typer.Option(
            "--reviewer",
            "-r",
            help="Requested reviewers (accepts multiple values)",
            show_default=False,
        ),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            "-pr",
            help="AI model provider",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="AI model",
        ),
    ] = None,
):
    try:
        git = get_git_client()
    except InvalidGitRepositoryError as err:
        print_error("Not valid a git repository")
        raise typer.Exit(1) from err

    chat_client = get_ai_client(model)
    chat_provider = prompt_for_chat_provider(chat_client, provider)
    chat_client.set_chat_model(chat_provider)

    gh = get_github_client(git.repo_name)

    latest_commit: Commit | None = None
    if git.is_dirty:
        commit_choice = inquirer.select(
            "You have uncommitted changes.",
            [
                "Commit and push with AI message",
                "Commit and push with manual message",
                "Proceed anyway",
            ],
        ).execute()
        match commit_choice:
            case "Commit and push with AI message":
                git.create_commit("chore: [dry run commit]", dry_run=True)
                rich.print("[grey70]Generating commit...[/]\n")
                commit_data = generate_commit_with_ai(chat_client, git)

                checkout_to_branch(git, chat_client, gh.default_branch, commit_data.message)
                latest_commit = git.create_commit(commit_data.message)
                git.push()
            case "Commit and push with manual message":
                git.create_commit("chore: [dry run commit]", dry_run=True)
                commit_message = typer.edit("")
                if not commit_message:
                    print_error("No commit message provided")
                    raise typer.Exit(0)

                checkout_to_branch(git, chat_client, gh.default_branch, commit_message)
                latest_commit = git.create_commit(commit_message)
                git.push()
            case "Proceed anyway":
                checkout_to_branch(git, chat_client, gh.default_branch, commit_message=None)
            case _:
                print_error("No matching choice for commit was provided")
                raise typer.Exit(1)

    if not git.confirm_branch_exists_in_remote():
        git.push()

    if not git.remote_branch_in_sync():
        confirm_push = typer.confirm(
            "Local branch is not up to date with remote. Push to remote now?"
        )
        if confirm_push:
            git.push()

    jira = get_jira_client()

    first_commit = git.get_first_commit_since_checkout()
    commit = latest_commit or first_commit

    jira_project = get_jira_project(jira, git.repo_name, project) if ticket else ""

    title = (
        first_commit.summary.decode()
        if isinstance(first_commit.summary, bytes)
        else first_commit.summary
    )
    body = _create_pr_body(commit, jira_project, ticket)

    selected_reviewers = prompt_for_reviewers(gh, reviewers, git.repo_name, draft)

    pr_template = gh.get_contents(".github/pull_request_template.md")
    diff_to_main = git.get_diff("main", gh.default_branch)
    rich.print("[grey70]Generating description...[/]")
    pr_description = generate_description(
        chat_client, pr_template, git.repo_name, diff_to_main, body, jira_project
    )

    if not ticket:
        ticket_choice = typer.prompt(
            "Ticket [enter #, enter (g) to generate, or Enter to skip]",
            default="",
            show_default=False,
        )
        if ticket_choice.lower() == "g":
            jira_project = jira_project or get_jira_project(jira, git.repo_name, project)
            rich.print("[grey70]Generating ticket...[/]\n")

            issuetypes = jira.get_issuetypes(jira_project)
            ticket_data = generate_ticket_with_ai(
                chat_client,
                git.repo_name,
                issuetypes=issuetypes,
                pr_description=pr_description,
            )

            myself_ref = get_user_from_jira(jira, user_query=None, user_type="reporter")

            jira_issue = jira.create_ticket(
                jira_project,
                ticket_data.issuetype,
                ticket_data.summary,
                ticket_data.description,
                myself_ref,
                myself_ref,
            )
            ticket = jira_issue.key.split("-")[1]
        elif ticket_choice.isdigit():
            ticket = ticket_choice
            jira_project = jira_project or get_jira_project(jira, git.repo_name, project)
        else:
            pass

    if pr_description and ticket and jira_project:
        pr_description = _add_jira_key_to_description(pr_description, jira_project, ticket)

    pr = gh.create_pr(
        git.current_branch,
        title=title,
        body=pr_description or body or "",
        draft=draft,
    )

    if selected_reviewers:
        gh.add_reviewers_to_pr(pr, selected_reviewers)

    rich.print(f"\n[grey70]{pr_description}[/]\n")
    rich.print(f":rocket: Created PR in [blue]{git.repo_name}[/] with title [bold green]{title}[/]")
    rich.print(f"[dark violet]https://github.com/{git.repo_name}/pull/{pr.number}[/]")

    if not ticket:
        return

    ticket_id = format_jira_ticket(jira_project, ticket or "")

    try:
        transitions = jira.get_transitions(ticket_id)

        if JIRA_IN_PROGRESS_TRANSITION in transitions:
            jira.transition_issue(ticket_id, JIRA_IN_PROGRESS_TRANSITION)
            transitions = jira.get_transitions(ticket_id)

        if not draft and JIRA_READY_FOR_REVIEW_TRANSITION in transitions:
            jira.transition_issue(ticket_id, JIRA_READY_FOR_REVIEW_TRANSITION)
            rich.print(f":eyes: Moved issue [blue]{ticket_id}[/] to [green]Ready for review[/]")
    except JIRAError as err:
        rich.print(err)
        raise typer.Exit(1) from err


def _create_pr_body(commit: Commit, jira_key: str, ticket: str | None) -> str | None:
    commit_message = commit.message if isinstance(commit.message, str) else commit.message.decode()
    try:
        body = (
            commit_message.replace(
                commit.summary if isinstance(commit.summary, str) else commit.summary.decode(),
                "",
            )
            .lstrip()
            .rstrip()
        )
    except IndexError:
        body = None

    if not ticket:
        return body

    ticket_str = format_jira_ticket(jira_key, ticket)
    if not body:
        return f"[{ticket_str}]"

    if ticket_str in body:
        return body

    return body.replace(ticket, f"[{ticket_str}]")


def _add_jira_key_to_description(text: str, jira_project: str, jira_key: str | int) -> str:
    """
    Search for any substring matching [{jira_project}-NUMBERS/LETTERS] (e.g. [ABC-XX1234]
    or ABC-XX1234) and replace each occurrence with the formatted Jira key.

    Args:
        text: The input string to search.
        jira_key: The Jira key to substitute in place of each [...] match.

    Returns:
        A new string with all [LETTERS-NUMBERS] patterns replaced.
    """
    pattern = rf"\[?{jira_project}-[A-Za-z0-9]+\]?"
    formatted_key = format_jira_ticket(jira_project, jira_key, with_brackets=True)

    if formatted_key in text:
        return text  # already present

    if re.search(pattern, text) is not None:
        return re.sub(pattern, formatted_key, text)

    return f"{text}\n\n{jira_key}"
