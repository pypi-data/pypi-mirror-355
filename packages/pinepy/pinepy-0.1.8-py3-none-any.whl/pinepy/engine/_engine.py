import logging
import sys
from queue import Queue
from threading import Thread
from typing import Callable, Generator, TypeAlias

import polars as pl

from ._models import ColName, EnvState, FrameWindow, LiveFrame, Strategy, _bar_columns

ErrHandler: TypeAlias = Callable[[Exception], None]

_logger = logging.getLogger("pinepy")
_handler = logging.StreamHandler(stream=sys.stdout)
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


class LiveTransport:
    def __init__(self):
        self._input = Queue[LiveFrame | None]()

    def append_frame(self, frame: LiveFrame):
        self._input.put(frame)

    def stop(self):
        self._input.put(None)


class FrameEngine:
    def _roll_window(
        self,
        strategy: Strategy,
        state: EnvState,
        window: FrameWindow,
        warm_window: FrameWindow | None = None,
    ):
        data = window.data
        warm_index = strategy.warm_up
        end_index = warm_index
        if warm_window is not None:
            data = warm_window.data.tail(warm_index).vstack(data, in_place=True)
        state.is_live = False
        for i in range(end_index):
            data_partial = data.slice(0, i + 1)
            strategy._pre_next(data_partial)
        while end_index < data.height:
            data_partial = data.slice(0, end_index + 1)
            strategy._pre_next(data_partial)
            state.bar_index = end_index
            strategy.next(
                open=data_partial[ColName.open],
                high=data_partial[ColName.high],
                low=data_partial[ColName.low],
                close=data_partial[ColName.close],
                volume=data_partial[ColName.volume],
                ts=data_partial[ColName.ts],
                extend=data_partial.select(pl.exclude(_bar_columns)),
                state=state,
            )
            end_index += 1

    def backtest(
        self,
        strategy: Strategy,
        state: EnvState,
        window_generator: Generator[FrameWindow, None, None],
    ):
        """
        warm window could bigger than all window, backtest cannot tell it in advance
        """
        last_window: FrameWindow | None = None
        for window in window_generator:
            if last_window is None and window.data.height < strategy.warm_up:
                _logger.warning(
                    "Warm up window is smaller than warm up period, "
                    "would not run for the first window"
                )
            self._roll_window(strategy, state, window, last_window)
            last_window = window

    def live(
        self,
        strategy: Strategy,
        state: EnvState,
        warm_frames: FrameWindow,
        err_handler: ErrHandler,
        window_size: int = 500,
    ) -> LiveTransport:
        self._roll_window(strategy, state, warm_frames)
        data = warm_frames.data
        bar_index = len(data) - 1
        warm = strategy.warm_up
        transport = LiveTransport()
        if warm > window_size:
            window_size = warm + 10

        def run_loop():
            nonlocal data, bar_index
            state.is_live = True
            _logger.info("engine live trade started")
            while True:
                try:
                    tick_append: LiveFrame | None = transport._input.get()
                    if tick_append is None:
                        break
                    data.vstack(pl.DataFrame(tick_append.row), in_place=True)
                    strategy._pre_next(data)
                    bar_index += 1
                    if data.height > warm:
                        state.bar_index = bar_index
                        strategy.next(
                            open=data[ColName.open],
                            high=data[ColName.high],
                            low=data[ColName.low],
                            close=data[ColName.close],
                            volume=data[ColName.volume],
                            ts=data[ColName.ts],
                            extend=data.select(pl.exclude(_bar_columns)),
                            state=state,
                        )
                    if data.shape[0] >= 2 * window_size:
                        data = data.tail(window_size)
                except Exception as e:
                    try:
                        err_handler(e)
                    except Exception as e:
                        _logger.error("Error handler error", exc_info=True)

            _logger.info("engine live trade stopped")

        Thread(target=run_loop).start()
        return transport
