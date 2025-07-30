from typing import TypedDict


class DbConfig(TypedDict):
    user: str
    password: str
    db: str
    host: str


class Config(TypedDict):
    db: DbConfig
