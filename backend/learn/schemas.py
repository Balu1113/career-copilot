from typing import Literal

from pydantic import BaseModel, Field


class TutorBlock(BaseModel):
    type: Literal[
        "heading",
        "paragraph",
        "code",
        "bullet_list",
        "numbered_list",
    ] = "paragraph"

    text: str = ""

    language: str = ""

    code: str = ""

    items: list[str] = Field(default_factory=list)


class TutorChatResponse(BaseModel):
    blocks: list[TutorBlock] = Field(default_factory=list)

    practice_question: str = ""

    suggested_questions: list[str] = Field(
        default_factory=list
    )
