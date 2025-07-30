# Installation Guide

This guide will help you install DataLineagePy and get it running on your system.

## 🚀 Quick Installation

The fastest way to get started:

```bash
pip install datalineagepy
```

That's it! DataLineagePy is now ready to use.

## 📋 System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 512MB available RAM
- **Storage**: 50MB free disk space

### Recommended Requirements

- **Python**: 3.9+ (for best performance)
- **Memory**: 2GB+ RAM (for large datasets)
- **Storage**: 200MB+ free space (for caching)

## 📦 Installation Options

### Option 1: Basic Installation (Recommended)

```bash
pip install datalineagepy
```

Includes:

- Core lineage tracking
- DataFrame wrapper
- Basic visualizations
- Testing framework

### Option 2: Full Installation (All Features)

```bash
pip install datalineagepy[all]
```

Includes everything plus:

- Advanced ML features
- Real-time alerting
- Enhanced visualizations
- Performance profiling
- Export capabilities

### Option 3: Development Installation

```bash
git clone https://github.com/yourusername/DataLineagePy.git
cd DataLineagePy
pip install -e ".[dev]"
```

Includes:

- Full feature set
- Development tools
- Testing dependencies
- Documentation tools

## 🔧 Feature-Specific Installations

### Visualization Features

```bash
pip install datalineagepy[viz]
```

Adds: Plotly, Bokeh, advanced charting

### ML & Anomaly Detection

```bash
pip install datalineagepy[ml]
```

Adds: Scikit-learn, anomaly detection models

### Real-time Alerting

```bash
pip install datalineagepy[alerts]
```

Adds: Slack, email, webhook notifications

### Performance Profiling

```bash
pip install datalineagepy[profiling]
```

Adds: Memory profilers, performance benchmarks

## ✅ Verify Installation

Test your installation with this simple script:

```python
import datalineagepy
from datalineagepy import LineageTracker, DataFrameWrapper
import pandas as pd

# Check version
print(f"DataLineagePy version: {datalineagepy.__version__}")

# Quick functionality test
tracker = LineageTracker()
df = pd.DataFrame({'test': [1, 2, 3]})
df_wrapped = DataFrameWrapper(df, tracker=tracker, name="test_data")

print("✅ DataLineagePy installed successfully!")
```

Expected output:

```
DataLineagePy version: 1.0.0
✅ DataLineagePy installed successfully!
```

## 🐍 Virtual Environment Setup (Recommended)

### Using conda

```bash
# Create environment
conda create -n datalineage python=3.9
conda activate datalineage

# Install DataLineagePy
pip install datalineagepy
```

### Using venv

```bash
# Create environment
python -m venv datalineage-env

# Activate (Windows)
datalineage-env\Scripts\activate

# Activate (macOS/Linux)
source datalineage-env/bin/activate

# Install DataLineagePy
pip install datalineagepy
```

## 🔄 Upgrading DataLineagePy

### Upgrade to Latest Version

```bash
pip install --upgrade datalineagepy
```

### Upgrade with All Features

```bash
pip install --upgrade datalineagepy[all]
```

### Check Current Version

```python
import datalineagepy
print(datalineagepy.__version__)
```

## 🛠️ Dependencies

DataLineagePy automatically installs these core dependencies:

### Core Dependencies

- **pandas** (≥1.3.0) - DataFrame operations
- **networkx** (≥2.6) - Graph operations
- **numpy** (≥1.21.0) - Numerical computing

### Optional Dependencies

- **plotly** (≥5.0.0) - Interactive visualizations
- **graphviz** (≥0.19.0) - Graph rendering
- **scikit-learn** (≥1.0.0) - ML anomaly detection
- **requests** (≥2.25.0) - HTTP notifications

## 🚨 Troubleshooting

### Common Installation Issues

#### Issue 1: Permission Denied

```bash
# Solution: Use --user flag
pip install --user datalineagepy
```

#### Issue 2: Python Version Too Old

```
ERROR: Package requires Python >=3.8
```

**Solution**: Upgrade Python to 3.8 or higher

#### Issue 3: Dependency Conflicts

```bash
# Solution: Use fresh environment
python -m venv fresh-env
source fresh-env/bin/activate  # Linux/macOS
# OR
fresh-env\Scripts\activate  # Windows
pip install datalineagepy
```

#### Issue 4: ImportError After Installation

```python
# Check if installation is in correct location
import sys
print(sys.path)

# Reinstall if needed
pip uninstall datalineagepy
pip install datalineagepy
```

### Getting Help

If you encounter issues:

1. **Check our [FAQ](faq.md)** for common solutions
2. **Search [GitHub Issues](https://github.com/yourusername/DataLineagePy/issues)**
3. **Create a new issue** with:
   - Python version (`python --version`)
   - OS and version
   - Full error message
   - Installation command used

## 🔐 Security Considerations

### Corporate Networks

If installing behind a corporate firewall:

```bash
# Use corporate proxy
pip install --proxy http://proxy.company.com:8080 datalineagepy

# Use corporate certificate bundle
pip install --cert /path/to/certificate.pem datalineagepy
```

### Air-Gapped Environments

For offline installation:

1. Download wheel file on connected machine:

   ```bash
   pip download datalineagepy
   ```

2. Transfer files to air-gapped machine

3. Install offline:
   ```bash
   pip install datalineagepy-*.whl
   ```

## 📈 Performance Optimization

### For Large Datasets

```bash
# Install with performance optimizations
pip install datalineagepy[performance]
```

### Memory-Constrained Environments

```bash
# Minimal installation
pip install datalineagepy --no-deps
pip install pandas networkx numpy  # Only core deps
```

## 🎯 Next Steps

Now that DataLineagePy is installed:

1. **[Quick Start Tutorial](quickstart.md)** - Your first lineage in 30 seconds
2. **[Core Concepts](user-guide/concepts.md)** - Understand how it works
3. **[Basic Examples](examples/basic.md)** - Learn common patterns

---

**Need help?** Check our [troubleshooting guide](troubleshooting.md) or create an [issue on GitHub](https://github.com/yourusername/DataLineagePy/issues).
