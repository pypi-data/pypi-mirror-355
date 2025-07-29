from typing import Callable, TypeAlias

import polars as pl

CalcBar: TypeAlias = Callable[[pl.DataFrame], list[float]]
