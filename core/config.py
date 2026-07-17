import json
from pathlib import Path
from typing import TypedDict

__all__ = ('Config', 'ResolvedConfig')


class ResolvedConfig(TypedDict):
    prefix: str
    token: str
    pg_dsn: str
    remove_default_help: bool


class ConfigReader:
    def __init__(self, name: str) -> None:
        self.path = Path(name)
        if not self.path.exists():
            raise FileNotFoundError(f'The config file: {name} could not be found.')
        if self.path.is_dir():
            raise FileNotFoundError(
                f'The config path cannot be a directory. (provided: {name})'
            )

    def read(self) -> ResolvedConfig:
        config: dict[str, str] = {}
        file_name: str = self.path.name
        with Path.open(file_name) as file:
            contents = file.read()
            config = json.loads(contents)

        prefix = config['prefix']
        token = config['token']
        pg_dsn = config['pg_dsn']
        remove_default_help = bool(config['remove_default_help'])

        return ResolvedConfig(
            prefix=prefix,
            token=token,
            pg_dsn=pg_dsn,
            remove_default_help=remove_default_help,
        )


class Config:
    def __init__(self, name: str = 'Config.json') -> None:
        self.reader = ConfigReader(name)
        self.config_dict = self.reader.read()

        self._prefix: str = self.config_dict['prefix']
        self._token: str = self.config_dict['token']
        self._pg_dsn: str = self.config_dict['pg_dsn']
        self._remove_default_help: bool = self.config_dict['remove_default_help']

    @property
    def prefix(self) -> str:
        return self._prefix

    @property
    def token(self) -> str:
        return self._token

    @property
    def pg_dsn(self) -> str:
        return self._pg_dsn

    @property
    def remove_default_help(self) -> bool:
        return self._remove_default_help
