from typing import NamedTuple, Union


class Env(NamedTuple):
    env_name: str
    env_type: Union[str, int]
    env_default: Union[str, int, None]
