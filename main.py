import os
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, TypeAdapter
from pathlib import Path


class Groups(BaseModel):
    id: int
    name: str
    link: str | None
    subjects: list[str]


class Lesson(BaseModel):
    start: str
    end: str


logger = logging.getLogger("uvicorn")

os.system("ls")
groups_file = Path("./data/group.json")
schedule_file = Path("./data/schedule.json")
call_schedule_file = Path("./data/call_schedule.json")

groups = TypeAdapter(list[Groups]).validate_json(groups_file.read_text())
schedule = TypeAdapter(dict[str, dict[str, list[str]]]).validate_json(
    schedule_file.read_text()
)
call_schedule = TypeAdapter(list[Lesson]).validate_json(call_schedule_file.read_text())

groups_by_id = {group.id: group for group in groups}
groups_by_name = {group.name: group for group in groups}

origin = os.getenv("ORIGIN", "http://127.0.0.1:5500")
logger.info(f"Origin: {origin}")


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


def found_group_by_id(id: int):
    try:
        return groups_by_id[id]
    except KeyError:
        return None


def found_group_by_name(name: str):
    try:
        return groups_by_name[name]
    except KeyError:
        return None


@app.get("/groups")
def get_groups():
    return groups


@app.get("/call_schedule")
def get_call_schedule():
    return call_schedule


@app.get("/group/by_id/{id}")
def get_group_by_id(id: int):
    group = found_group_by_id(id)
    if group:
        return group
    else:
        raise HTTPException(status_code=404, detail=f"Group with id:{id} doesn't exist")


@app.get("/group/by_name/{name}")
def get_group_by_name(name: str):
    group = found_group_by_name(name)
    if group:
        return group
    else:
        raise HTTPException(
            status_code=404, detail=f"Group with name:{name} doesn't exist"
        )


@app.get("/group/schedule/by_id/{id}")
def get_group_schedule_by_id(id: int):
    group = found_group_by_id(id)
    if group:
        return schedule[group.name]
    else:
        raise HTTPException(status_code=404, detail=f"Group with id:{id} doesn't exist")


@app.get("/group/schedule/by_name/{name}")
def get_group_schedule_by_name(name: str):
    group = found_group_by_name(name)
    if group:
        return schedule[group.name]
    else:
        raise HTTPException(
            status_code=404, detail=f"Group with name:{name} doesn't exist"
        )
