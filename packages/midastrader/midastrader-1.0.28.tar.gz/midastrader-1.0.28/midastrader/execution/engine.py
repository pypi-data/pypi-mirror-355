import threading
from enum import Enum
from typing import Dict

from midastrader.message_bus import MessageBus
from midastrader.structs.symbol import SymbolMap
from midastrader.utils.logger import SystemLogger
from midastrader.config import Parameters, Mode
from midastrader.execution.adaptors import IBAdaptor, DummyAdaptor


class Executors(Enum):
    IB = "interactive_brokers"
    DUMMY = "dummy"

    @staticmethod
    def from_str(value: str) -> "Executors":
        match value.lower():
            case "interactive_brokers":
                return Executors.IB
            case "dummy":
                return Executors.DUMMY
            case _:
                raise ValueError(f"Unknown vendor: {value}")

    def adapter(self):
        """Map the enum to the appropriate adapter class."""
        if self == Executors.IB:
            return IBAdaptor
        elif self == Executors.DUMMY:
            return DummyAdaptor
        else:
            raise ValueError(f"No adapter found for vendor: {self.value}")


class ExecutionEngine:
    def __init__(
        self,
        symbols_map: SymbolMap,
        message_bus: MessageBus,
        mode: Mode,
        parameters: Parameters,
    ):
        self.logger = SystemLogger.get_logger()
        self.message_bus = message_bus
        self.parameters = parameters
        self.symbol_map = symbols_map
        self.mode = mode

        self.adapters = []
        self.threads = []  # List to track threads
        self.completed = threading.Event()  # Event to signal completion
        self.running = threading.Event()

    def initialize_adaptors(self, executors: Dict[str, dict]) -> bool:
        if self.mode == Mode.BACKTEST:
            return self.initialize_dummy()
        else:
            return self.initialize_live(executors)

    def initialize_live(self, executors: Dict[str, dict]) -> bool:
        for e in executors.keys():
            if e != "dummy":
                adapter = Executors.from_str(e).adapter()
                self.adapters.append(
                    adapter(
                        self.symbol_map,
                        self.message_bus,
                        **executors[e],
                    )
                )

        return True

    def initialize_dummy(self) -> bool:
        self.adapters.append(
            DummyAdaptor(
                self.symbol_map,
                self.message_bus,
                self.parameters.capital,
            )
        )
        return True

    def start(self):
        """Start adapters in seperate threads."""
        self.logger.info("Execution-engine starting ...")

        for adapter in self.adapters:
            # Start the threads for each vendor
            thread = threading.Thread(target=adapter.process, daemon=True)
            self.threads.append(thread)
            thread.start()
            adapter.is_running.wait()

        # Start a monitoring thread to check when all adapter threads are done
        threading.Thread(target=self._monitor_threads, daemon=True).start()
        self.logger.info("Execution-engine running ...\n")
        self.running.set()

    def _monitor_threads(self):
        """
        Monitor all adapter threads and signal when all are done.
        """
        for thread in self.threads:
            thread.join()

        self.logger.info(
            "ExecutionEngine threads completed, shutting down ..."
        )
        self.completed.set()

    def wait_until_complete(self):
        """
        Wait for the engine to complete processing.
        """
        self.completed.wait()

    def stop(self):
        """Start adapters in separate threads."""

        for adapter in self.adapters:
            adapter.shutdown_event.set()
            adapter.is_shutdown.wait()
