import mbinary
from dataclasses import dataclass
from mbinary import PRICE_SCALE

from midastrader.structs.symbol import SecurityType


@dataclass
class Trade:
    """
    Represents a single trade event with details about execution, price, cost, and fees.

    Attributes:
        timestamp (int): The timestamp of the trade, typically in Unix epoch time.
        trade_id (int): Unique identifier for the trade.
        leg_id (int): Identifier for the leg (part of a multi-leg trades).
        instrument (int): Identifier for the traded instrument, e.g., ticker ID.
        quantity (float): The amount of the instrument traded.
        avg_price (float): The average execution price of the trade. Must be > 0.
        trade_value (float): The total notional value (quantity × price) of the trade.
        trade_cost (float): The total cost associated with entering the trade. (e.g., trade_value for equities, initial margin for futures, premium for options).
        action (str): Type of trade, e.g., "BUY", "SELL", "LONG", "SHORT", "COVER".
        fees (float): Fees incurred for the trade.
    """

    timestamp: int
    trade_id: int
    signal_id: int
    instrument: int
    security_type: SecurityType
    quantity: float
    avg_price: float
    trade_value: float
    trade_cost: float
    action: str  # BUY/SELL
    fees: float
    is_rollover: bool

    def __post_init__(self):
        """
        Post-initialization method to validate field types and values.

        Raises:
            TypeError: If a field is not of the expected type.
            ValueError: If 'action' is invalid or 'avg_price' is <= 0.
        """
        # Type Check
        if not isinstance(self.timestamp, int):
            raise TypeError("'timestamp' field must be of type int.")
        if not isinstance(self.trade_id, int):
            raise TypeError("'trade_id' field must be of type int.")
        if not isinstance(self.signal_id, int):
            raise TypeError("'signal_id' field must be of type int.")
        if not isinstance(self.instrument, int):
            raise TypeError("'instrument' field must be of type int.")
        if not isinstance(self.security_type, SecurityType):
            raise TypeError("'security_type' must be of type SecurityType.")
        if not isinstance(self.quantity, float):
            raise TypeError("'quantity' field must be of type float.")
        if not isinstance(self.avg_price, float):
            raise TypeError("'avg_price' field must be of type float.")
        if not isinstance(self.trade_value, float):
            raise TypeError("'trade_value' field must be of type float.")
        if not isinstance(self.trade_cost, float):
            raise TypeError("'trade_cost' field must be of type float.")
        if not isinstance(self.action, str):
            raise TypeError("'action' field must be of type str.")
        if not isinstance(self.fees, float):
            raise TypeError("'fees' field must be of type float.")
        if not isinstance(self.is_rollover, bool):
            raise TypeError("'is_rollover' field must be of type bool.")

        # Value Constraint
        if self.action not in ["BUY", "SELL", "LONG", "SHORT", "COVER"]:
            raise ValueError(
                "'action' field must be in ['BUY', 'SELL', 'LONG', 'SHORT', 'COVER']."
            )
        if self.avg_price <= 0:
            raise ValueError("'avg_price' field must be greater than zero.")

    def to_dict(self):
        """
        Converts the Trade object into a dictionary.

        Returns:
            dict: A dictionary representation of the Trade object.
        """
        return {
            "timestamp": int(self.timestamp),
            "trade_id": self.trade_id,
            "signal_id": self.signal_id,
            "ticker": self.instrument,
            "security_type": self.security_type.value,
            "quantity": self.quantity,
            "avg_price": self.avg_price,
            "trade_value": self.trade_value,
            "trade_cost": self.trade_cost,
            "action": self.action,
            "fees": self.fees,
            "is_rollover": self.is_rollover,
        }

    def to_mbinary(self, ticker: str) -> mbinary.Trades:
        """
        Converts the Trade object into a custom binary structure.

        Args:
            ticker (str): The instrument ticker to associate with the trade.

        Returns:
            mbinary.Trades: A custom binary trade object.
        """
        return mbinary.Trades(
            trade_id=self.trade_id,
            signal_id=self.signal_id,
            timestamp=self.timestamp,
            ticker=ticker,
            quantity=int(self.quantity * PRICE_SCALE),
            avg_price=int(self.avg_price * PRICE_SCALE),
            trade_value=int(self.trade_value * PRICE_SCALE),
            trade_cost=int(self.trade_cost * PRICE_SCALE),
            action=self.action,
            fees=int(self.fees * PRICE_SCALE),
        )

    def pretty_print(self, indent: str = "") -> str:
        """
        Generates a formatted string representation of the Trade object.

        Args:
            indent (str): Optional string for indentation.

        Returns:
            str: A human-readable formatted string of trade details.
        """
        return (
            f"{indent}Timestamp: {self.timestamp}\n"
            f"{indent}Trade ID: {self.trade_id}\n"
            f"{indent}Signal ID: {self.signal_id}\n"
            f"{indent}Instrument: {self.instrument}\n"
            f"{indent}Quantity: {self.quantity}\n"
            f"{indent}Avg Price: {self.avg_price}\n"
            f"{indent}Notional Value: {self.trade_value}\n"
            f"{indent}Trade Cost: {self.trade_cost}\n"
            f"{indent}Action: {self.action}\n"
            f"{indent}Fees: {self.fees}\n"
        )
