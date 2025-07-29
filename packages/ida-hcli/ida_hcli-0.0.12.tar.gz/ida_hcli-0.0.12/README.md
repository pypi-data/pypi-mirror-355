# IDA HCLI

A modern command-line interface for managing IDA Pro licenses, plugins, and cloud services.

[![PyPI version](https://badge.fury.io/py/ida-hcli.svg)](https://badge.fury.io/py/ida-hcli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Built with Hatch](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

## Installation

Install using `uv`:

Install globally
```bash
uvx ida-hcli
```

Install as a tool
```bash
uv tool install ida-hcli
```

Run directly 
```bash
uvx ida-hcli
```


## Quick Start

```bash
# Login to your Hex-Rays account
hcli login

# Check your authentication status
hcli whoami

# Browse and install plugins
hcli plugin browse
hcli plugin install <plugin-name>

# Manage your licenses
hcli license list

# Use cloud analysis
hcli cloud analyze <binary-file>
```

## Commands

- **Authentication**: `hcli login`, `hcli logout`, `hcli whoami`
- **Plugin Management**: `hcli plugin list|search|install|uninstall|browse`
- **License Management**: `hcli license list|get|install`
- **Cloud Services**: `hcli cloud analyze`, `hcli cloud session list`
- **File Sharing**: `hcli share put|get|list|delete`
- **IDA Configuration**: `hcli ida config get|set|list|delete`

## Configuration

The CLI stores configuration in your system's standard config directory:
- Linux/macOS: `~/.config/hcli/`
- Windows: `%APPDATA%\hcli\`

Set environment variables for advanced configuration:
- `HCLI_API_KEY`: Use API key authentication instead of OAuth
- `HCLI_DEBUG`: Enable debug output
- `HCLI_API_URL`: Override default API endpoint

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to:

- Report bugs and suggest features
- Submit pull requests with proper testing
- Set up your development environment with Hatch
- Generate and update documentation automatically

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Issues and Support

- **Bug Reports & Feature Requests**: [GitHub Issues](https://github.com/HexRaysSA/ida-hcli/issues)
- **Questions & Discussions**: [GitHub Discussions](https://github.com/HexRaysSA/ida-hcli/discussions)
- **Documentation**: Auto-generated from source code at build time
- **Commercial Support**: Contact support@hex-rays.com
- **Hex-Rays Website**: [hex-rays.com](https://hex-rays.com/)

## Development

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/HexRaysSA/ida-hcli.git
cd ida-hcli

# Install dependencies
uv sync

# Run in development mode
uv run hcli --help
```

### Build System

This project uses **Hatch** as the build backend with automated tooling:

```bash
# Install with development dependencies
uv sync

# Build package
uv run python -m build

# Run development tools
uv run ruff check        # Linting
uv run mypy src/         # Type checking
uv run pytest           # Testing
```

### Documentation

Documentation is **automatically generated** from source code:

```bash
# Build documentation
uv run mkdocs build

# Serve documentation locally
uv run mkdocs serve

# Documentation includes:
# - CLI commands (from Click help text)
# - API reference (from Python docstrings)
# - Usage examples (auto-generated)
```

### Testing

```bash
# Run tests
uv run pytest

# Test CLI commands
uv run hcli whoami
uv run hcli plugin list
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.