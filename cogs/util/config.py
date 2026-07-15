from typing import TypedDict
from pathlib import Path
import json


class ResolvedConfig(TypedDict):
    prefix: str
    token: str
    pg_dsn: str
    remove_default_help: bool


class ConfigReader:
    def __init__(self, name: str = "Config.json") -> None:
        self.path = Path(name)
        if not self.path.exists():
            raise FileNotFoundError(
                "The config file: {} could not be found.".format(name)
            )
        elif self.path.is_dir():
            raise FileNotFoundError(
                "The config path cannot be a directory. (provided: {})".format(name)
            )

    def read(self) -> ResolvedConfig:
        config: dict[str, str] = {}
        file_name: str = self.path.name
        with open(file_name) as file:
            contents = file.read()
            deserialized_file = json.loads(contents)
            config = deserialized_file

        prefix = config["prefix"]
        token = config["token"]
        pg_dsn = config["pg_dsn"]
        remove_default_help = bool(config["remove_default_help"])

        config_obj = ResolvedConfig(
            prefix=prefix,
            token=token,
            pg_dsn=pg_dsn,
            remove_default_help=remove_default_help,
        )
        return config_obj


class Config:
    def __init__(self, name: str = "Config.json") -> None:
        self.reader = ConfigReader(name)
        self.config_dict = self.reader.read()

        self._prefix = self.config_dict["prefix"]
        self._token = self.config_dict["token"]
        self._pg_dsn = self.config_dict["pg_dsn"]
        self._remove_default_help = self.config_dict["remove_default_help"]

    @property
    def prefix(self):
        return self._prefix

    @property
    def token(self):
        return self._token

    @property
    def pg_dsn(self):
        return self._pg_dsn

    @property
    def remove_default_help(self):
        return self._remove_default_help
