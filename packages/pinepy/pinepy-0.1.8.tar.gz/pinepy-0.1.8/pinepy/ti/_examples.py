from polars import DataFrame
from talipp import indicators
from talipp.ohlcv import OHLCVFactory

from ..engine._models import ColName, Indicator
from ._models import CalcBar


class EMA(Indicator):
    def __init__(
        self,
        ema_len: int = 3,
        calc: CalcBar | None = None,
    ):
        self.len = ema_len
        if calc is None:

            def c(data: DataFrame):
                return data[ColName.close].to_list()

            self.calc = c
        else:
            self.calc = calc

    def var(self):
        return self.ema.output_values

    def next(self, data: DataFrame):
        if data.height > 1:
            self.ema.add(self.calc(data.tail(1)))
        else:
            self.ema = indicators.EMA(self.len, self.calc(data))
        if len(self.ema) >= 2 * self.len:
            self.ema.purge_oldest(self.len)


class SMA(Indicator):
    def __init__(
        self,
        sma_len: int = 3,
        calc: CalcBar | None = None,
    ):
        self.len = sma_len
        if calc is None:

            def c(data: DataFrame):
                return data[ColName.close].to_list()

            self.calc = c
        else:
            self.calc = calc
        self.sma = indicators.SMA(self.len, [])

    def var(self):
        return self.sma.output_values

    def next(self, data: DataFrame):
        self.sma.add(self.calc(data.tail(1)))


class HeikinAshi(Indicator):
    def __init__(self) -> None:
        self.ha_close, self.ha_open, self.ha_high, self.ha_low = [], [], [], []

    def next(self, data: DataFrame):
        open, high, low, close = (
            data[ColName.open][-1],
            data[ColName.high][-1],
            data[ColName.low][-1],
            data[ColName.close][-1],
        )
        self.ha_open.append(
            0 if data.height <= 1 else (self.ha_open[-1] + self.ha_close[-1]) / 2
        )
        self.ha_close.append((open + high + low + close) / 4)
        self.ha_high.append(max(high, self.ha_open[-1], self.ha_close[-1]))
        self.ha_low.append(min(low, self.ha_open[-1], self.ha_close[-1]))

    def var(self):
        return (
            self.ha_open,
            self.ha_high,
            self.ha_low,
            self.ha_close,
        )


class CCI(Indicator):
    def __init__(
        self,
        cci_len: int = 14,
        cci_ma_len: int = 3,
    ):
        self.len = cci_len
        self.ma_len = cci_ma_len
        self.cci = indicators.CCI(
            period=self.len,
            input_values=OHLCVFactory.from_dict(
                {
                    "high": [],
                    "low": [],
                    "close": [],
                }
            ),
        )
        self.cci_ma = indicators.SMA(
            period=self.ma_len, input_values=self.cci.output_values
        )

    def var(self):
        return self.cci.output_values, self.cci_ma.output_values

    def next(self, data: DataFrame):
        d = data.tail(1)
        self.cci.add(
            OHLCVFactory.from_dict(
                {
                    "high": d[ColName.high].to_list(),
                    "low": d[ColName.low].to_list(),
                    "close": d[ColName.close].to_list(),
                }
            )
        )
        self.cci_ma.add(self.cci.output_values[-1])
