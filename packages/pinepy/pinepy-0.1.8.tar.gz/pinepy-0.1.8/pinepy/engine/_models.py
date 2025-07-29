import logging
import sys
from abc import ABCMeta, abstractmethod
from typing import Any, Literal, TypeAlias

import polars as pl

FrameCols: TypeAlias = Literal["open", "high", "low", "close", "volume", "ts"]


class ColName:
    open = "open"
    high = "high"
    low = "low"
    close = "close"
    volume = "volume"
    ts = "ts"


_bar_columns = [
    i
    for i in [
        ColName.open,
        ColName.high,
        ColName.low,
        ColName.close,
        ColName.volume,
        ColName.ts,
    ]
]
_must_have_set = set(_bar_columns)
WRONG_COLUMN = ValueError("data must have columns: {}".format(_bar_columns))

_logger = logging.getLogger("strategy")
_handler = logging.StreamHandler(stream=sys.stdout)
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


class FrameWindow:
    def __init__(self, data: pl.DataFrame):
        if not _must_have_set.issubset(set(data.columns)):
            raise WRONG_COLUMN
        self.data = data


class LiveFrame:
    def __init__(
        self,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        ts: int,
        extend: dict[str, Any] | None = None,
    ):
        """
        due to polars, we can't use list in one row, so we wrap list in list,
        it would be converted to pl.list
        """
        self.ts = ts
        self.row = {
            ColName.open: open,
            ColName.high: high,
            ColName.low: low,
            ColName.close: close,
            ColName.volume: volume,
            ColName.ts: ts,
        }
        if extend is not None:
            for k, v in extend.items():
                if isinstance(v, list):
                    extend[k] = [v]
            self.row.update(extend)


class Indicator(metaclass=ABCMeta):
    @abstractmethod
    def var(self) -> Any:
        pass

    @abstractmethod
    def next(self, data: pl.DataFrame):
        pass


class EnvState:
    def __init__(self, symbol: str, interval: str):
        self.is_live = False
        self.bar_index = 0
        self.symbol = symbol
        self.interval = interval


class Strategy(metaclass=ABCMeta):
    """
    you can choose which time to init broker,
    for example, you can init broker in __init__, then you can use self.broker in next() with fixed logic
    or you can init when you create different variable of Strategy to backtest or live trade,
    and recognize the condition(backtest or live trade) in next() to use different broker
    """

    def init(self, warm_up: int, name: str, use_indicators: list[Indicator]):
        self.warm_up = warm_up
        self.name = name
        self._indicators = use_indicators
        _logger = logging.getLogger(name)
        _handler = logging.StreamHandler(stream=sys.stdout)
        _handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        _logger.addHandler(_handler)
        _logger.setLevel(logging.DEBUG)
        self.log = _logger

    def _pre_next(self, data: pl.DataFrame):
        for i in self._indicators:
            i.next(data)

    @abstractmethod
    def next(
        self,
        open: pl.Series,
        high: pl.Series,
        low: pl.Series,
        close: pl.Series,
        volume: pl.Series,
        ts: pl.Series,
        extend: pl.DataFrame,
        state: EnvState,
    ):
        pass
