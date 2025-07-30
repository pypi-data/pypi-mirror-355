from typing import Union, Any, Dict, Literal, List
from .optimization import Study
from .types import Param


def range(
    a: Union[float, int],
    b: Union[float, int],
    log_scale: bool = False,
    dtype: Union[type, Literal["auto"]] = "auto",
) -> Param:
    if dtype == "auto":
        if isinstance(a, float) or isinstance(b, float):
            dtype = float
        elif isinstance(a, int) and isinstance(b, int):
            dtype = int

    if dtype not in (float, int):
        raise TypeError("Invalid type for range")

    a = dtype(a)
    b = dtype(b)

    if a > b:
        a, b = b, a

    return Param("numeric", bounds=(a, b), log_scale=log_scale, dtype=dtype)


def ordinal(values: List[Any]) -> Param:
    return Param("ordinal", values=values)


def choice(options: List[Any]) -> Param:
    return Param("categorical", values=options)


def minimize(objective: str, params: Dict[str, Param]) -> Study:
    return Study(objective, "minimize", params)


def maximize(objective: str, params: Dict[str, Param]) -> Study:
    return Study(objective, "maximize", params)


def load(path: str) -> Study:
    return Study.load(path)
