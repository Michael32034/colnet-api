import os
import json
import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import TypeAdapter
from pathlib import Path
from psycopg import AsyncConnection
from psycopg.rows import TupleRow, class_row, dict_row

from db import Database, Lesson, Group, ReplacementRecord, tablename

logger = logging.getLogger("uvicorn")

call_schedule_file = Path("./data/call_schedule.json")
call_schedule = TypeAdapter(list[Lesson]).validate_json(call_schedule_file.read_text())

conn_string = os.environ.get(
    "DB", "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable"
)

origins = os.getenv("ORIGINS", "http://127.0.0.1:5500").split()
logger.info(f"Origins: {origins}")


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)
db = Database(conn_string)


DBDep = Annotated[AsyncConnection[TupleRow], Depends(db.get_conn)]


@app.get("/groups")
async def get_groups(conn: DBDep) -> list[Group]:
    async with conn.cursor(row_factory=class_row(Group)) as cur:
        groups = await (
            await cur.execute(t"SELECT name, link, subjects FROM {tablename:i};")
        ).fetchall()
        return groups


@app.get("/call_schedule")
def get_call_schedule():
    return call_schedule


@app.get("/group/by_name/{name}")
async def get_group_by_name(name: str, conn: DBDep) -> Group:
    async with conn.cursor(row_factory=class_row(Group)) as cur:
        group = await (
            await cur.execute(
                t"SELECT name, link, subjects FROM {tablename:i} WHERE name = {name};"
            )
        ).fetchone()
    if group:
        return group
    else:
        raise HTTPException(
            status_code=404, detail=f"Group with name:{name} doesn't exist"
        )


@app.get("/group/schedule/by_name/{name}")
async def get_group_schedule_by_name(name: str, conn: DBDep) -> dict[str, list[str]]:
    async with conn.cursor() as cur:
        schedule = await (
            await cur.execute(
                t"SELECT schedule FROM {tablename:i} WHERE name = {name};"
            )
        ).fetchone()
    if schedule:
        return schedule[0]
    else:
        raise HTTPException(
            status_code=404, detail=f"Group with name:{name} doesn't exist"
        )


@app.get("/group/replacement/by_name/{name}")
async def get_group_schedule(name: str, conn: DBDep) -> list[ReplacementRecord]:
    async with conn.cursor(row_factory=dict_row) as cur:
        replacements = await (await cur.execute(t"""SELECT
                    group_name, date, lessons, audience, content
                FROM 
                    replacement
                WHERE group_name = {name} AND date=CURRENT_DATE;""")).fetchall()
    if replacements:
        return TypeAdapter(list[ReplacementRecord]).validate_python(replacements)
    else:
        return []
