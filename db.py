from datetime import date
from psycopg import AsyncConnection
from psycopg.rows import TupleRow
from psycopg.types.json import Jsonb
from collections.abc import AsyncIterator
from pydantic import BaseModel, TypeAdapter

tablename = "college_groups"


class Group(BaseModel):
    name: str
    link: str | None
    subjects: list[str]


class Lesson(BaseModel):
    start: str
    end: str

class Subject(BaseModel):
    name: str
    teacher: str


class Replacement(BaseModel):
    old: Subject
    new: Subject


class ReplacementRecord(BaseModel):
    group_name: str
    date: date
    lessons: str
    audience: str
    content: str | Replacement

class Database:
    conn_string: str

    def __init__(self, conn_string):
        self.conn_string = conn_string

    async def get_conn(self) -> AsyncIterator[AsyncConnection[TupleRow]]:
        async with await AsyncConnection.connect(self.conn_string) as conn:
            yield conn
