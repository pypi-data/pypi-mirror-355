# ruff: noqa: ARG002, E501, C901
import datetime as dt
import json
import os
import random
from dataclasses import dataclass
from typing import Literal, overload

import pytest
import toml
from git import Commit, HookExecutionError
from github.CheckRun import CheckRun
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview
from jira import Issue, Project
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, TypeAdapter

from glu import ROOT_DIR
from glu.config import JIRA_SERVER, Config, EnvConfig, RepoConfig
from glu.models import ChatProvider, IdReference, JiraUser
from tests import TESTS_DATA_DIR
from tests.utils import load_json


class FakeJiraClient:
    def myself(self) -> JiraUser:
        return JiraUser("2662", "peter")

    def projects(self) -> list[Project]:
        @dataclass
        class FakeProject:
            key: str

        return [FakeProject("TEST"), FakeProject("GLU")]  # type: ignore

    def search_users(self, query: str) -> list[JiraUser]:
        return [
            JiraUser("5234", "jack"),
            JiraUser("3462", "teddy"),
            JiraUser("55462", "sarah"),
        ]

    def get_issuetypes(self, project: str) -> list[str]:
        return ["Bug", "Story", "Spike", "Chore", "Subtask"]

    def get_transitions(self, ticket_id: str) -> list[str]:
        if os.getenv("IS_JIRA_TICKET_IN_TO_DO"):
            return ["Starting"]
        if os.getenv("IS_JIRA_TICKET_IN_PROGRESS"):
            return ["Ready for review"]

        return []

    def transition_issue(self, ticket_id: str, transition: str) -> None:
        pass

    def create_ticket(
        self,
        project: str,
        issuetype: str,
        summary: str,
        description: str | None,
        reporter_ref: IdReference,
        assignee_ref: IdReference,
        **extra_fields: dict,
    ) -> Issue:
        @dataclass
        class FakeTicket:
            key: str

            def permalink(self) -> str:
                return f"{JIRA_SERVER}/browse/{self.key}"

        new_ticket = f"{project}-{random.randint(100, 1000)}"
        return FakeTicket(new_ticket)  # type: ignore


class FakeGitClient:
    def get_first_commit_since_checkout(self) -> Commit:
        @dataclass
        class FakeCommit:
            message: str

            @property
            def summary(self) -> str:
                return self.message.split("\n")[0]

        return FakeCommit("feat: Add testing to my CLI app")  # type: ignore

    def remote_branch_in_sync(self, branch: str | None = None, remote_name: str = "origin") -> bool:
        return os.getenv("IS_REMOTE_BRANCH_IN_SYNC") == "1"

    @overload
    def get_diff(self, to: Literal["head"]) -> str: ...

    @overload
    def get_diff(self, to: Literal["main"], default_branch: str) -> str: ...

    def get_diff(
        self, to: Literal["main", "head"] = "head", default_branch: str | None = None
    ) -> str:
        with open(TESTS_DATA_DIR / "diff_to_main.txt", "r") as f:
            return f.read()

    def create_commit(self, message: str, dry_run: bool = False, retry: int = 0) -> Commit:
        if os.getenv("RAISE_HOOK_EXECUTION_ERROR"):
            raise HookExecutionError(
                "commit",
                """
            glu/local.py:275:19: ARG001 Unused function argument: `git`
                |
            275 | def create_commit(git: Git, message: str, dry_run: bool = False, retry: int = 0) -> Commit:
                |                   ^^^ ARG001
            276 |     try:
            277 |         local_repo.git.add(all=True)
                |
            """,
            )

        @dataclass
        class FakeCommit:
            summary: str
            message: str

        return FakeCommit(  # type: ignore
            "feat: Add testing to my CLI app",
            "- Add testing through pexpect and pytest\n- Added very many good tests",
        )

    def push(self) -> None:
        os.environ["IS_REMOTE_BRANCH_IN_SYNC"] = "1"
        pass

    def checkout(self, branch_name: str) -> None:
        pass

    def confirm_branch_exists_in_remote(self) -> bool:
        return True

    def get_commit_count_since_checkout(self, default_branch: str) -> int:
        return 5

    def get_commit_log(self, limit: int) -> list[Commit]:
        class CommitAuthor(BaseModel):
            name: str

        class FakeCommit(BaseModel):
            author: CommitAuthor
            summary: str
            hexsha: str
            committed_datetime: dt.datetime

        return TypeAdapter(list[FakeCommit]).validate_python(load_json("list_commits.json"))  # type: ignore

    @property
    def repo_name(self) -> str:
        return "github/Test-Repo"

    @property
    def current_branch(self) -> str:
        return "add-tests"

    @property
    def is_dirty(self) -> bool:
        return os.getenv("IS_GIT_DIRTY") == "1"


class FakeGithubClient:
    def __init__(self, repo_name: str):
        pass

    def get_members(self, repo_name: str) -> list[NamedUser]:
        @dataclass
        class FakeUser:
            login: str

        return [FakeUser("teddy"), FakeUser("jack"), FakeUser("peter")]  # type: ignore

    def create_pr(
        self,
        current_branch: str,
        title: str,
        body: str | None,
        draft: bool,
    ) -> PullRequest:
        @dataclass
        class FakePullRequest:
            number: int

        return FakePullRequest(random.randint(1000, 10_000))  # type: ignore

    def add_reviewers_to_pr(self, pr: PullRequest, reviewers: list[NamedUser]) -> None:
        pass

    def get_contents(self, path: str, ref: str | None = None) -> str | None:
        if os.getenv("HAS_REPO_TEMPLATE"):
            with open(ROOT_DIR / ".github" / "pull_request_template.md", "r") as f:
                return f.read()

        return None

    def get_pr(self, number: int) -> PullRequest:
        class FakePullRequest(BaseModel):
            number: int
            title: str
            body: str | None
            changed_files: int
            id: int
            mergeable: bool
            mergeable_state: str
            merged: bool
            updated_at: str
            state: str
            draft: bool

            def get_commits(self) -> list[Commit]:
                class FakeCommit(BaseModel):
                    message: str

                class FakeCommitRef(BaseModel):
                    commit: FakeCommit

                @dataclass
                class PaginatedList:
                    totalCount: int

                    def get_page(self, page: int) -> list[PullRequestReview]:
                        if page > 0:
                            return []

                        prev_commits = load_json("previous_commit_messages.json")
                        commits = [{"commit": {"message": message}} for message in prev_commits]

                        return TypeAdapter(list[FakeCommitRef]).validate_python(commits)  # type: ignore

                return PaginatedList(4)  # type: ignore

            def merge(
                self, commit_message: str, commit_title: str, merge_method: str, delete_branch: bool
            ) -> None:
                pass

            def get_reviews(self) -> PaginatedList[PullRequestReview]:
                class NamedUser(BaseModel):
                    login: str

                class PRReview(BaseModel):
                    id: int
                    body: str | None
                    state: str
                    user: NamedUser

                @dataclass
                class PaginatedList:
                    totalCount: int

                    def get_page(self, page: int) -> list[PullRequestReview]:
                        if page > 0:
                            return []

                        pr_reviews = load_json("pr_reviews.json")
                        if os.getenv("IS_PR_NOT_APPROVED"):
                            pr_reviews.pop(-1)
                        if os.getenv("PR_CHANGES_REQUESTED"):
                            pr_reviews[1]["state"] = "CHANGES_REQUESTED"
                            pr_reviews[1]["body"] = "meh /:"

                        return TypeAdapter(list[PRReview]).validate_python(pr_reviews)  # type: ignore

                return PaginatedList(2)  # type: ignore

            def mark_ready_for_review(self):
                pass

        pr_data = load_json("pr_data.json")
        if os.getenv("PR_NOT_MERGEABLE"):
            pr_data["mergeable"] = False
            pr_data["mergeable_state"] = "dirty"

        if os.getenv("IS_PR_MERGED"):
            pr_data["merged"] = True

        if os.getenv("IS_DRAFT_PR"):
            pr_data["draft"] = True

        return FakePullRequest.model_validate(pr_data)  # type: ignore

    def get_pr_checks(self, number: int) -> list[CheckRun]:
        class FakeCheckRun(BaseModel):
            id: int
            status: str
            completed: bool
            conclusion: str
            name: str
            started_at: dt.datetime

        checks = load_json("cicd_run_checks.json")
        if os.getenv("IS_CICD_FAILING"):
            checks[-1]["conclusion"] = "failure"

        return TypeAdapter(list[FakeCheckRun]).validate_python(checks)  # type: ignore

    @property
    def default_branch(self) -> str:
        return "main"


class FakeChatClient:
    providers: list[ChatProvider] = []
    model: str | None = None
    _client: BaseChatModel | None = None

    def __init__(self, model: str | None):
        self.providers = ["OpenAI", "Ollama"]
        self.model = model

    def run(self, msg: str) -> str:
        if "adding testing" in msg:
            return json.dumps(load_json("ai_ticket.json"))
        if "Provide a commit message for the following diff" in msg:
            return json.dumps(load_json("commit_message.json"))
        if "Provide the issue type for a Jira ticket" in msg:
            return "Chore"
        if "Provide a description and summary for a Jira" in msg:
            return json.dumps(load_json("ai_ticket.json"))
        if "Provide a description for the PR diff below." in msg:
            with open(TESTS_DATA_DIR / "pr_description.txt", "r") as f:
                return f.read()
        if "Provide a commit message for merge into the repo." in msg:
            return json.dumps(load_json("final_commit_message.json"))
        raise NotImplementedError("AI test message not implemented")

    def set_chat_model(self, provider: ChatProvider | None) -> None:
        pass


@pytest.fixture
def write_base_config():
    default_config = Config(env=EnvConfig.defaults())
    path = TESTS_DATA_DIR / "config.toml"
    path.write_text(toml.dumps(default_config.model_dump()), encoding="utf-8")


@pytest.fixture
def write_config_w_repo_config():
    default_config = Config(
        env=EnvConfig.defaults(),
        repos={"github/Test-Repo": RepoConfig(jira_project_key="TEST")},
    )
    path = TESTS_DATA_DIR / "config.toml"
    path.write_text(toml.dumps(default_config.model_dump()), encoding="utf-8")


@pytest.fixture
def env_cli():
    env = os.environ.copy()
    env["TERM"] = "dumb"
    env["GLU_TEST"] = "1"
    env["VISUAL"] = "vim"
    return env
