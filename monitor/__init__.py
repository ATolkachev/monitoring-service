from typing import NamedTuple, Any

__version__ = '1.0.1'


class Env(NamedTuple):
    env_name: str
    env_type: Any[str, int]
    env_default: Any[str, int, None]
