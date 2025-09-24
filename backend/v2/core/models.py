from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class Prompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: str = "system"
    tags: str = ""
    versions: List["PromptVersion"] = Relationship(back_populates="prompt")

class PromptVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_id: int = Field(foreign_key="prompt.id")
    body: str
    created_at: datetime = datetime.utcnow()
    prompt: Prompt = Relationship(back_populates="versions")

class KBFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    path: str
    status: str = "ready"
    chunks: List["KBChunk"] = Relationship(back_populates="file")

class KBChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    file_id: int = Field(foreign_key="kbfile.id")
    text: str
    vector: bytes = b""
    file: KBFile = Relationship(back_populates="chunks")

class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_s: float = 0.0
    status: str = "success"
    created_at: datetime = datetime.utcnow()

class Setting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str
    value: str
