# 📊 Stockholm Finance

> **Note**: Pre-commit hooks are now active! 🎉

[![CI/CD Pipeline](https://github.com/aykaym/stockholm/actions/workflows/ci.yml/badge.svg)](https://github.com/aykaym/stockholm/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/stockholm-finance.svg)](https://badge.fury.io/py/stockholm-finance)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://github.com/aykaym/stockholm/pkgs/container/stockholm)

> **Advanced financial sentiment analysis tool with policy impact assessment, intelligent caching, and professional dashboard interface.**

## 🚀 Quick Start

### Installation

```bash
# From PyPI
pip install stockholm-finance

# From source
git clone https://github.com/aykaym/stockholm.git
cd stockholm
pip install -e .
```

### Docker

```bash
# Run with Docker
docker run -it ghcr.io/aykaym/stockholm:latest

# Development environment
docker-compose up dev
```

### Command Line Usage

```bash
# Launch the interactive financial analysis dashboard
stockholm-finance

# With options
stockholm-finance --quick      # Quick mode for faster startup
stockholm-finance --verbose    # Verbose output with debug info
```

### Python API Usage

```python
# Launch the dashboard programmatically
from src.core.financial_analyzer import main
main()

# Or use the dashboard directly
from src.ui.textual_dashboard import run_textual_dashboard
run_textual_dashboard()

# With configuration options
from src.ui.textual_dashboard import run_enhanced_textual_dashboard
run_enhanced_textual_dashboard(quick_mode=True, verbose=True)
```

## ✨ Features

### 🎯 **Core Analysis**
- **Sentiment Analysis**: Advanced NLP for market sentiment from news articles
- **Policy Analysis**: Government policy impact assessment on markets
- **Multi-Ticker Support**: Analyze sentiment across multiple stocks simultaneously
- **Real-time Data**: Live market data integration with yfinance

### 💾 **Smart Caching**
- **TTL-based Caching**: Intelligent cache expiration (15min news, 5min prices)
- **Performance Optimization**: 50+ cache reads/second, 20+ writes/second
- **Storage Efficiency**: Compressed JSON storage with automatic cleanup

### 📊 **Interactive Dashboard**
- **Professional TUI**: Rich terminal interface with real-time updates
- **Multiple Views**: Ticker info, earnings data, price charts, sentiment analysis
- **Responsive Design**: Adaptive layouts for different terminal sizes

### 🧪 **Enterprise Testing**
- **37+ Tests**: Comprehensive test suite with 100% pass rate
- **Coverage**: 80% cache manager, 68% policy analyzer, 39% sentiment analyzer
- **Performance**: Benchmarked at 10+ articles/second processing

## 📋 Requirements

- **Python**: 3.8 or higher
- **Dependencies**: See `requirements.txt`
- **Optional**: Docker for containerized deployment

## 🏗️ Architecture

```
stockholm/
├── src/
│   ├── core/           # Core analysis engines
│   ├── data/           # Data fetching and caching
│   ├── ui/             # User interface components
│   └── config/         # Configuration management
├── tests/              # Comprehensive test suite
├── docs/               # Documentation
├── scripts/            # DevOps and utility scripts
└── .github/            # CI/CD workflows
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html

# Performance tests
python -m pytest tests/test_performance.py -v

# Use the coverage checker
python check_coverage.py
```

## 🚀 Development

### Local Setup

```bash
# Clone repository
git clone https://github.com/yourusername/stockholm.git
cd stockholm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

### Docker Development

```bash
# Development environment
docker-compose up dev

# Run tests in container
docker-compose up test

# Code quality checks
docker-compose up quality
```

## 📦 Releases

### Automated Releases

The project uses automated versioning and releases:

```bash
# Create new release
python scripts/release.py

# Choose release type:
# - patch: Bug fixes (1.0.0 → 1.0.1)
# - minor: New features (1.0.0 → 1.1.0)  
# - major: Breaking changes (1.0.0 → 2.0.0)
```

### CI/CD Pipeline

- ✅ **Automated Testing**: All Python versions (3.8-3.12)
- ✅ **Security Scanning**: Bandit + Safety vulnerability checks
- ✅ **Code Quality**: Black, isort, flake8, mypy
- ✅ **Docker Images**: Multi-platform builds
- ✅ **GitHub Releases**: Automatic changelog generation

## 📊 Performance

### Benchmarks

- **Sentiment Analysis**: 10+ articles/second
- **Cache Performance**: 50+ reads/second, 20+ writes/second
- **Memory Usage**: <100MB for 1000 articles
- **Test Suite**: 37 tests in <1 second

### Scalability

- **Concurrent Processing**: Multi-threaded analysis support
- **Batch Operations**: Efficient bulk data processing
- **Memory Efficient**: Optimized for large datasets

## 🔒 Security

- **Dependency Scanning**: Automated vulnerability checks
- **Code Analysis**: Static security analysis with Bandit
- **Input Validation**: Sanitized data processing
- **No Secrets**: No hardcoded API keys or credentials

## 📖 Documentation

- **[Complete Documentation](docs/README.md)**: Comprehensive user guide
- **[Testing Guide](docs/TESTING.md)**: Testing strategy and coverage
- **[DevOps Guide](docs/DEVOPS.md)**: CI/CD and deployment
- **[Coverage Report](docs/COVERAGE.md)**: Code coverage analysis

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes with tests
4. **Run** quality checks (`black src/ tests/ && pytest`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TextBlob**: Natural language processing
- **yfinance**: Financial data API
- **Textual**: Modern terminal UI framework
- **Rich**: Beautiful terminal formatting
- **pytest**: Testing framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/aykaym/stockholm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aykaym/stockholm/discussions)
- **Documentation**: [Project Docs](docs/README.md)

---

**Built with ❤️ for the financial analysis community**
