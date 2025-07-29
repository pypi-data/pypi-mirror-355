import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass
class Config:
    host: str
    port: int
    server: str
    token: str
    default_playlists: list[str]
    cache_size: int
    news: bool
    player: str

    @classmethod
    def load(cls, path: Path) -> Self:
        with open(path, "r") as config_file:
            config = json.load(config_file)

        return cls(
            config["host"],
            config["port"],
            config["server"],
            config["token"],
            config["default_playlists"],
            config["cache_size"],
            config["news"],
            config["player"],
        )
