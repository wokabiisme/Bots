# AI Trading System - Enterprise Grade

A production-ready, modular AI-powered algorithmic trading system capable of trading Forex, Crypto, Stocks, Indices, and Commodities across multiple exchanges.

## Features

### Multi-Asset Support
- **Forex** - MT5, OANDA, Interactive Brokers
- **Crypto** - Binance, Bybit, Coinbase Advanced
- **Stocks** - Interactive Brokers, Alpaca
- **Indices** - MT5, Interactive Brokers
- **Commodities** - MT5, Interactive Brokers

### AI Engine
- XGBoost, LightGBM, Random Forest, CatBoost ensemble models
- LSTM/GRU/Transformer neural networks
- Reinforcement Learning agents
- Automatic weekly retraining
- Feature engineering and importance analysis

### Technical Analysis
- 20+ indicators (RSI, MACD, EMA, SMA, VWAP, ATR, ADX, Bollinger Bands, Ichimoku, etc.)
- Smart Money Concepts (Order Blocks, FVG, Liquidity Sweeps)
- Market Structure analysis
- Volume Profile
- Support/Resistance identification

### Risk Management
- Configurable per-trade risk limits
- Daily/Weekly/Monthly loss caps
- Maximum drawdown protection
- Position sizing (Kelly Criterion)
- Correlation filters
- Circuit breaker system
- Emergency shutdown

### Execution
- Multi-strategy simultaneous execution
- Order retry mechanisms
- Partial closes and scaling
- OCO orders support
- Multiple timeframe analysis
- News-aware trading

### Backtesting & Optimization
- Walk-forward analysis
- Monte Carlo simulation
- Genetic Algorithm optimization
- Optuna hyperparameter tuning
- Bayesian optimization
- Parameter sweep capabilities

### Dashboard & Monitoring
- Real-time FastAPI + React dashboard
- Live P&L tracking
- Open positions monitoring
- Risk metrics
- AI confidence scores
- Multi-channel alerts (Telegram, Discord, Slack, Email, SMS)

### Data Collection
- Automated historical data download
- Tick data ingestion
- Economic calendar integration
- News sentiment analysis
- COT reports
- Whale transactions tracking
- Exchange flows monitoring

## Project Structure

```
TradingBot/
├── config/                 # Configuration files
├── strategies/             # Strategy implementations
├── ai/                     # AI/ML engine
├── backtesting/            # Backtesting engine
├── execution/              # Order execution
├── risk/                   # Risk management
├── dashboard/              # Web dashboard
├── database/               # Database layer
├── logs/                   # Application logs
├── optimization/           # Optimization algorithms
├── news/                   # News integration
├── sentiment/              # Sentiment analysis
├── technical/              # Technical indicators
├── fundamental/            # Fundamental data
├── utils/                  # Utility functions
├── models/                 # ML models storage
├── tests/                  # Unit & integration tests
├── docker/                 # Docker configuration
└── requirements.txt        # Python dependencies
```

## Installation

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose
- 8GB+ RAM

### Quick Start

1. Clone the repository
```bash
git clone https://github.com/wokabiisme/Bots.git
cd Bots
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. Initialize database
```bash
python database/init_db.py
```

6. Run with Docker Compose
```bash
docker-compose up -d
```

## Usage

### Start the trading system
```bash
python main.py
```

### Run backtesting
```bash
python backtesting/backtest.py --strategy MyStrategy --symbol EURUSD --start 2023-01-01 --end 2024-01-01
```

### Optimize strategy
```bash
python optimization/optimize.py --strategy MyStrategy --metric sharpe
```

### Access dashboard
```
http://localhost:8000
```

## Configuration

All configuration is managed in `config/` directory using YAML files:

- `config/main.yaml` - Core settings
- `config/strategies.yaml` - Strategy parameters
- `config/risk.yaml` - Risk management rules
- `config/brokers.yaml` - Broker API credentials
- `config/logging.yaml` - Logging configuration

## Security

- API keys stored in environment variables
- Encrypted database credentials
- Role-based access control
- Audit logging
- Rate limiting on all endpoints
- Automatic backups

## Testing

Run tests:
```bash
pytest tests/ -v --cov
```

## Documentation

See `/docs` for detailed documentation on:
- Strategy development
- AI model training
- Risk management
- API integration
- Deployment

## Support

For issues and questions, open a GitHub issue or contact the development team.

## License

MIT License

## Disclaimer

This system is provided for educational and research purposes. Trading involves substantial risk. Always use proper risk management and paper trading before live deployment.
