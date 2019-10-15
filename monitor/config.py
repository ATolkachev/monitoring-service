from typing import NamedTuple, Union, Callable


class Env(NamedTuple):
    env_name: str
    env_type: Callable
    env_default: Union[str, int, None]
