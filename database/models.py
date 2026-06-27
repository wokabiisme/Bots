"""SQLAlchemy database models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, Enum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class TradeStatus(str, enum.Enum):
    """Trade status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderType(str, enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(str, enum.Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("Account", back_populates="user")
    trades = relationship("Trade", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )


class Account(Base):
    """Trading account model."""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    broker = Column(String(50), nullable=False)  # MT5, Binance, Bybit, etc.
    account_number = Column(String(100), nullable=False)
    account_type = Column(String(20), nullable=False)  # live, demo, paper
    balance = Column(Float, default=0)
    equity = Column(Float, default=0)
    margin = Column(Float, default=0)
    margin_level = Column(Float, default=0)
    free_margin = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="accounts")
    trades = relationship("Trade", back_populates="account")
    positions = relationship("Position", back_populates="account")
    
    __table_args__ = (
        Index('idx_account_user_broker', 'user_id', 'broker'),
        Index('idx_account_number', 'account_number'),
    )


class Strategy(Base):
    """Trading strategy model."""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    strategy_type = Column(String(50), nullable=False)  # momentum, scalping, swing, etc.
    parameters = Column(JSON, default={})
    is_active = Column(Boolean, default=False)
    win_rate = Column(Float, default=0)
    profit_factor = Column(Float, default=0)
    max_drawdown = Column(Float, default=0)
    sharpe_ratio = Column(Float, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    trades = relationship("Trade", back_populates="strategy")
    
    __table_args__ = (
        Index('idx_strategy_user', 'user_id'),
        Index('idx_strategy_active', 'is_active'),
    )


class Trade(Base):
    """Trade execution model."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.PENDING)
    profit_loss = Column(Float, default=0)
    profit_loss_percent = Column(Float, default=0)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    duration_seconds = Column(Integer)
    commission = Column(Float, default=0)
    slippage = Column(Float, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trades")
    account = relationship("Account", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    orders = relationship("Order", back_populates="trade")
    
    __table_args__ = (
        Index('idx_trade_user', 'user_id'),
        Index('idx_trade_account', 'account_id'),
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_status', 'status'),
        Index('idx_trade_entry_time', 'entry_time'),
    )


class Order(Base):
    """Order execution model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'), nullable=False)
    order_id = Column(String(100), unique=True, nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    price = Column(Float)
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0)
    status = Column(String(50), nullable=False)
    commission = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    
    # Relationships
    trade = relationship("Trade", back_populates="orders")
    
    __table_args__ = (
        Index('idx_order_trade', 'trade_id'),
        Index('idx_order_id', 'order_id'),
        Index('idx_order_symbol', 'symbol'),
    )


class Position(Base):
    """Open position model."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_profit = Column(Float, default=0)
    unrealized_profit_percent = Column(Float, default=0)
    margin_used = Column(Float, default=0)
    opened_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    
    __table_args__ = (
        Index('idx_position_account', 'account_id'),
        Index('idx_position_symbol', 'symbol'),
    )


class CandleData(Base):
    """OHLCV candlestick data model."""
    __tablename__ = "candle_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_candle_symbol_timeframe', 'symbol', 'timeframe'),
        Index('idx_candle_timestamp', 'timestamp'),
    )


class TickData(Base):
    """Tick data model."""
    __tablename__ = "tick_data"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False)
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    bid_volume = Column(Float)
    ask_volume = Column(Float)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tick_symbol', 'symbol'),
        Index('idx_tick_timestamp', 'timestamp'),
    )


class Economic Event(Base):
    """Economic calendar event model."""
    __tablename__ = "economic_events"
    
    id = Column(Integer, primary_key=True)
    country = Column(String(10), nullable=False)
    event_name = Column(String(200), nullable=False)
    forecast = Column(Float)
    previous = Column(Float)
    actual = Column(Float)
    importance = Column(String(20))  # low, medium, high
    release_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_event_country', 'country'),
        Index('idx_event_release_time', 'release_time'),
    )


class News(Base):
    """News article model."""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    source = Column(String(100), nullable=False)
    url = Column(String(500))
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Float)  # -1 to 1
    keywords = Column(JSON, default=[])
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_news_published', 'published_at'),
        Index('idx_news_sentiment', 'sentiment'),
    )


class ModelPerformance(Base):
    """AI model performance tracking."""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    training_time_seconds = Column(Float)
    trained_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_model_name', 'model_name'),
        Index('idx_model_trained', 'trained_at'),
    )


class AISignal(Base):
    """AI trading signal model."""
    __tablename__ = "ai_signals"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), nullable=False)
    signal_type = Column(String(20), nullable=False)  # buy, sell, hold
    confidence = Column(Float, nullable=False)  # 0-1
    models_voted = Column(Integer)
    models_agreed = Column(Integer)
    reasoning = Column(Text)
    price_at_signal = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_signal_symbol', 'symbol'),
        Index('idx_signal_created', 'created_at'),
    )


class AuditLog(Base):
    """Audit logging model."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_created', 'created_at'),
    )
