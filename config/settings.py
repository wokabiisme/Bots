"""Application settings using Pydantic."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str = Field(default="postgresql://postgres:password@localhost:5432/trading_bot")
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=40)
    echo: bool = Field(default=False)
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    url: str = Field(default="redis://localhost:6379/0")
    cache_expire: int = Field(default=3600)
    
    class Config:
        env_prefix = "REDIS_"


class SecuritySettings(BaseSettings):
    """Security configuration."""
    secret_key: str = Field(default="your-secret-key-change-in-production")
    api_key_encryption_key: str = Field(default="your-encryption-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    
    class Config:
        env_prefix = "SECRET_"


class BrokerSettings(BaseSettings):
    """Broker API configurations."""
    # MetaTrader 5
    mt5_login: Optional[str] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    
    # Binance
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None
    
    # Bybit
    bybit_api_key: Optional[str] = None
    bybit_api_secret: Optional[str] = None
    bybit_testnet_key: Optional[str] = None
    bybit_testnet_secret: Optional[str] = None
    
    # Coinbase
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None
    coinbase_passphrase: Optional[str] = None
    
    # Interactive Brokers
    ib_account: Optional[str] = None
    ib_username: Optional[str] = None
    ib_password: Optional[str] = None
    ib_port: int = 7497
    
    # OANDA
    oanda_api_key: Optional[str] = None
    oanda_account_id: Optional[str] = None
    oanda_environment: str = "practice"
    
    # Alpaca
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_base_url: str = "https://paper-trading.alpaca.markets"
    
    class Config:
        env_prefix = ""


class NotificationSettings(BaseSettings):
    """Notification configuration."""
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # Discord
    discord_webhook_url: Optional[str] = None
    
    # Slack
    slack_webhook_url: Optional[str] = None
    
    # Email
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_address: Optional[str] = None
    email_password: Optional[str] = None
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_from: Optional[str] = None
    twilio_phone_to: Optional[str] = None
    
    class Config:
        env_prefix = ""


class TradingSettings(BaseSettings):
    """Trading configuration."""
    paper_trading: bool = True
    live_trading: bool = False
    max_open_positions: int = 10
    max_daily_loss_percent: float = 2.0
    max_weekly_loss_percent: float = 5.0
    max_monthly_loss_percent: float = 10.0
    max_drawdown_percent: float = 15.0
    risk_per_trade_percent: float = 1.0
    profit_factor_threshold: float = 2.0
    winrate_threshold: float = 0.45
    
    class Config:
        env_prefix = ""


class AISettings(BaseSettings):
    """AI/ML configuration."""
    model_retraining_frequency: str = "weekly"
    confidence_threshold: float = 0.65
    ensemble_models: List[str] = Field(default=["xgboost", "lightgbm", "catboost", "rf"])
    use_reinforcement_learning: bool = True
    use_deep_learning: bool = True
    
    class Config:
        env_prefix = "AI_"


class BacktestSettings(BaseSettings):
    """Backtesting configuration."""
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    initial_capital: float = 100000
    commission: float = 0.001
    slippage: float = 0.0005
    
    class Config:
        env_prefix = "BACKTEST_"


class DataCollectionSettings(BaseSettings):
    """Data collection configuration."""
    retention_days: int = 730
    charts_download_frequency: str = "daily"
    tick_data_collection: bool = True
    economic_calendar_sync: bool = True
    cot_report_sync: bool = True
    whale_transaction_monitoring: bool = True
    funding_rate_monitoring: bool = True
    
    class Config:
        env_prefix = "DATA_"


class Settings(BaseSettings):
    """Main application settings."""
    app_name: str = "AI_Trading_System"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    broker: BrokerSettings = BrokerSettings()
    notifications: NotificationSettings = NotificationSettings()
    trading: TradingSettings = TradingSettings()
    ai: AISettings = AISettings()
    backtest: BacktestSettings = BacktestSettings()
    data_collection: DataCollectionSettings = DataCollectionSettings()
    
    worker_count: int = 4
    max_retries: int = 3
    retry_delay_seconds: int = 5
    health_check_interval: int = 300
    automatic_recovery_enabled: bool = True
    emergency_shutdown_enabled: bool = True
    circuit_breaker_threshold: float = 0.1
    circuit_breaker_cooldown: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
