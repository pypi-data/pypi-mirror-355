from typing import Annotated, Any

import rich
import typer
from git import InvalidGitRepositoryError
from InquirerPy import inquirer
from typer import Context

from glu.ai import get_ai_client, prompt_for_chat_provider
from glu.config import DEFAULT_JIRA_PROJECT
from glu.jira import (
    generate_ticket_with_ai,
    get_jira_client,
    get_jira_project,
    get_user_from_jira,
)
from glu.local import get_git_client
from glu.utils import get_kwargs, prompt_or_edit

app = typer.Typer()


@app.command(
    short_help="Create a Jira ticket",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def create(
    ctx: Context,
    summary: Annotated[
        str | None,
        typer.Option(
            "--summary",
            "-s",
            "--title",
            help="Issue summary or title",
        ),
    ] = None,
    type: Annotated[str | None, typer.Option("--type", "-t", help="Issue type")] = None,
    body: Annotated[
        str | None,
        typer.Option("--body", "-b", help="Issue description"),
    ] = None,
    assignee: Annotated[str | None, typer.Option("--assignee", "-a", help="Assignee")] = None,
    reporter: Annotated[str | None, typer.Option("--reporter", "-r", help="Reporter")] = None,
    priority: Annotated[str | None, typer.Option("--priority", "-y", help="Priority")] = None,
    project: Annotated[str | None, typer.Option("--project", "-p", help="Jira project")] = None,
    ai_prompt: Annotated[
        str | None,
        typer.Option("--ai-prompt", "-ai", help="AI prompt to generate summary and description"),
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
    extra_fields: dict[str, Any] = get_kwargs(ctx)

    jira = get_jira_client()

    try:
        repo_name = get_git_client().repo_name
    except InvalidGitRepositoryError:
        repo_name = None

    project = project or DEFAULT_JIRA_PROJECT
    if not project:
        project = get_jira_project(jira, repo_name)

    types = jira.get_issuetypes(project or "")
    if not type:
        issuetype = inquirer.select("Select type:", types).execute()
    else:
        if type.title() not in types:
            issuetype = inquirer.select("Select type:", types).execute()
        else:
            issuetype = type

    if ai_prompt:
        # typer does not currently support union types
        # once they do, the below will work
        # keep an eye on: https://github.com/fastapi/typer/pull/1148
        # if isinstance(ai_prompt, bool):
        #     prompt = prompt_or_edit('AI Prompt')
        # else:
        # prompt = ai_prompt

        chat_client = get_ai_client(model)
        provider = prompt_for_chat_provider(chat_client, provider, True)
        chat_client.set_chat_model(provider)
        ticket_data = generate_ticket_with_ai(
            chat_client, repo_name, issuetype, ai_prompt=ai_prompt
        )
        summary = ticket_data.summary
        body = ticket_data.description
    else:
        if not summary:
            summary = typer.prompt(
                "Summary",
                show_default=False,
            )

        if not body:
            body = prompt_or_edit("Description", allow_skip=True)

    reporter_ref = get_user_from_jira(jira, reporter, "reporter")

    assignee_ref = get_user_from_jira(jira, assignee, "assignee")

    if priority:
        extra_fields["priority"] = priority

    issue = jira.create_ticket(
        project, issuetype, summary or "", body, reporter_ref, assignee_ref, **extra_fields
    )

    rich.print(f":page_with_curl: Created issue [bold red]{issue.key}[/]")
    rich.print(f"View at {issue.permalink()}")
