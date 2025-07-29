import queue
import threading
import pandas as pd
import importlib.util
from typing import Type
from typing import List
from abc import abstractmethod

from midastrader.structs.symbol import SymbolMap
from midastrader.structs.signal import SignalInstruction
from midastrader.message_bus import MessageBus, EventType
from midastrader.structs.events import SignalEvent, MarketEvent
from midastrader.core.adapters.order_book import OrderBook
from midastrader.core.adapters.portfolio import PortfolioServer
from midastrader.core.adapters.base import CoreAdapter


class BaseStrategy(CoreAdapter):
    """
    Abstract base class for trading strategies.

    This class provides a framework for processing market data, generating trading signals,
    and interacting with portfolio components. Specific strategies must inherit from
    this class and implement the abstract methods.

    Attributes:
        logger (SystemLogger): Logger for recording activity and debugging.
        symbols_map (SymbolMap): Mapping of instrument symbols to their corresponding data.
        order_book (OrderBook): Maintains and updates market data.
        portfolio_server (PortfolioServer): Handles portfolio operations, including positions and capital.
        hist_data_client (DataClient): Provides access to historical market data.
        historical_data (Any): Placeholder for loaded historical data.
    """

    def __init__(self, symbols_map: SymbolMap, bus: MessageBus):
        """
        Initializes the strategy with required components.

        Args:
            symbols_map (SymbolMap): Mapping of instrument symbols to `Symbol` objects.
            portfolio_server (PortfolioServer): The portfolio server for managing account and positions.
            order_book (OrderBook): The order book that maintains market data.
            hist_data_client (DataClient): Client for accessing historical market data.
        """
        super().__init__(symbols_map, bus)
        self.order_book = OrderBook.get_instance()
        self.portfolio_server = PortfolioServer.get_instance()
        self.historical_data = None
        self.threads = []

        # Subscribe to orderbook updates
        self.orderbook_queue = self.bus.subscribe(EventType.ORDER_BOOK)

    def process(self) -> None:
        """
        Handles incoming events and processes them according to the strategy logic.

        Args:
            subject (Subject): The subject that triggered the event.
            event_type (EventType): The type of the event (e.g., `MARKET_DATA`).
            event (MarketEvent): The market event containing data to process.
        """
        try:
            self.threads.append(
                threading.Thread(target=self.process_orderbook, daemon=True)
            )
            self.threads.append(
                threading.Thread(target=self.process_initial_data, daemon=True)
            )

            for thread in self.threads:
                thread.start()

            self.logger.info("Strategy running ...")
            self.is_running.set()

            for thread in self.threads:
                thread.join()

        finally:
            self.cleanup()

    def process_orderbook(self) -> None:
        """
        Handles incoming events and processes them according to the strategy logic.

        Args:
            subject (Subject): The subject that triggered the event.
            event_type (EventType): The type of the event (e.g., `MARKET_DATA`).
            event (MarketEvent): The market event containing data to process.
        """
        while not self.shutdown_event.is_set():
            try:
                event = self.orderbook_queue.get(timeout=0.01)
                self.handle_event(event)
            except queue.Empty:
                continue

    def process_initial_data(self) -> None:
        while not self.shutdown_event.is_set():
            if self.bus.get_flag(EventType.INITIAL_DATA):
                self.handle_initial_data()
                break

        self.logger.info("Strategy process initial data thread ending.")

    def cleanup(self):
        while True:
            try:
                event = self.orderbook_queue.get(timeout=1)
                self.handle_event(event)
            except queue.Empty:
                break

        self.logger.info("Shutting down Strategy ...")
        self.is_shutdown.set()

    @abstractmethod
    def handle_event(self, event: MarketEvent) -> None:
        pass

    # @abstractmethod
    def handle_initial_data(self) -> None:
        pass

    @abstractmethod
    def get_strategy_data(self) -> pd.DataFrame:
        """
        Retrieves strategy-specific data.

        Returns:
            pd.DataFrame: A DataFrame containing relevant strategy-specific data.
        """
        pass

    def set_signal(
        self,
        trade_instructions: List[SignalInstruction],
        timestamp: int,
    ):
        """
        Creates and dispatches a signal event based on trade instructions.

        Args:
            trade_instructions (List[SignalInstruction]): A list of trade instructions to execute.
            timestamp (int): The time at which the signal is generated (in nanoseconds).

        Raises:
            RuntimeError: If signal creation fails due to invalid input or unexpected errors.
        """
        try:
            if len(trade_instructions) > 0:
                signal_event = SignalEvent(timestamp, trade_instructions)
                self.bus.publish(EventType.SIGNAL, signal_event)
                self.bus.publish(EventType.SIGNAL_UPDATE, signal_event)
            else:
                self.bus.publish(EventType.UPDATE_SYSTEM, False)

        except (ValueError, TypeError) as e:
            raise RuntimeError(f"Failed to set SignalEvent : {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error setting SignalEvent: {e}")


def load_strategy_class(
    module_path: str,
    class_name: str,
) -> Type[BaseStrategy]:
    """
    Dynamically loads a strategy class from a specified module and class name.

    Args:
        module_path (str): The file path to the module containing the strategy class.
        class_name (str): The name of the strategy class to load.

    Returns:
        Type[BaseStrategy]: The loaded strategy class.

    Raises:
        ValueError: If the specified class is not a subclass of `BaseStrategy`.
        AttributeError: If the class name does not exist in the module.
        ImportError: If the module cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("module.name", module_path)

    if spec is None:
        raise ImportError(f"Cannot load module from path: {module_path}")

    module = importlib.util.module_from_spec(spec)

    if spec.loader is None:
        raise ImportError(f"Module {module_path} has no valid loader.")

    spec.loader.exec_module(module)
    strategy_class = getattr(module, class_name)

    if not issubclass(strategy_class, BaseStrategy):
        raise ValueError(f"{class_name} must be derived from BaseStrategy.")

    return strategy_class
