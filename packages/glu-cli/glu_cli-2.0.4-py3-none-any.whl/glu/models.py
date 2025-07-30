from dataclasses import dataclass
from typing import Literal

from github.NamedUser import NamedUser
from pydantic import BaseModel, model_validator

ChatProvider = Literal["OpenAI", "Glean", "Gemini", "Anthropic", "xAI", "Ollama"]

CHAT_PROVIDERS: list[ChatProvider] = ["OpenAI", "Glean", "Gemini", "Anthropic", "xAI", "Ollama"]

TICKET_PLACEHOLDER = "[XY-1234]"


@dataclass
class MatchedUser:
    user: NamedUser
    score: float


class TicketGeneration(BaseModel):
    description: str
    summary: str
    issuetype: str


class IdReference(BaseModel):
    id: str


@dataclass
class JiraUser:
    accountId: str
    displayName: str


class CommitGeneration(BaseModel):
    title: str
    body: str
    type: str

    @model_validator(mode="after")
    def validate_title(self) -> "CommitGeneration":
        if self.type in self.title:
            self.title = self.title.split(":")[1].strip()

        self.title = self.title.capitalize()
        return self

    @property
    def message(self):
        return f"{self.type}: {self.title}\n\n{self.body}"
