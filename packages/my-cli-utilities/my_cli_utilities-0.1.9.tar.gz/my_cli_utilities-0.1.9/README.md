# My CLI Utilities

A suite of powerful CLI tools for interacting with Account Pool and Device Spy services. This package provides two main utilities: `ap` for account management and `ds` for device management.

## 🚀 Features

- **Account Pool CLI (`ap`)**: Manage and query accounts from the account pool service
- **Device Spy CLI (`ds`)**: Monitor and interact with devices in the device spy system
- **User-friendly interface**: Beautiful emoji-enhanced output with pagination
- **Smart caching**: Index-based access for faster operations
- **Flexible search**: Support for various query patterns including IP suffix matching

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install my-cli-utilities
```

### From Source
```bash
git clone <repository-url>
cd my-cli-utilities
pip install .
```

### Development Installation
```bash
git clone <repository-url>
cd my-cli-utilities
make setup
```

## 🔧 Usage

### Account Pool CLI (`ap`)

#### Quick Start
```bash
# List available account types
ap types

# Get a random account by type name
ap get "kamino2(CI-Common-4U,mThor,brand=1210)"

# Get a random account by index (from types list)
ap get 2

# Get account details by phone number
ap info 12495002020

# Get account by ID
ap by_id 507f1f77bcf86cd799439011
```

#### Available Commands
- `ap types [filter] [brand]` - List account types with optional filtering
- `ap get <type|index> [env]` - Get random account by type or index
- `ap info <phone> [env]` - Get account details by phone number
- `ap by_id <id> [env]` - Get account details by ID
- `ap cache [clear]` - Manage cache (view status or clear)
- `ap help` - Show detailed help

### Device Spy CLI (`ds`)

#### Quick Start
```bash
# Get device information
ds udid A1B2C3D4E5F6

# List available devices
ds devices android
ds devices ios

# Find hosts
ds host lab                 # Search by keyword
ds host .201               # Search by IP suffix
ds host XMNA067            # Search by alias
```

#### Available Commands
- `ds info <udid>` - Get detailed device information
- `ds devices <platform>` - List available devices (android/ios)
- `ds host <query>` - Find host by various criteria
- `ds help` - Show detailed help

## 💡 Advanced Features

### Smart Caching
The account pool CLI automatically caches account types for faster access:
```bash
ap types           # Cache account types
ap get 5          # Use index instead of long type name
ap cache          # View cache status
ap cache clear    # Clear cache
```

### Flexible Host Search
The device spy CLI supports multiple search patterns:
```bash
ds host 192.168    # Find hosts containing IP pattern
ds host .201       # Find hosts ending with .201
ds host lab        # Find hosts with 'lab' in any field
ds host 15.4       # Find hosts with macOS version 15.4
```

### Pagination
Both tools support interactive pagination for long lists:
- Press Enter to continue to next page
- Type 'q' to quit viewing

## 🛠️ Development

### Setup Development Environment
```bash
make setup          # Install dev dependencies
make build          # Build the package
make install-dev    # Install in editable mode
```

### Build and Release
```bash
make build          # Build package
make upload-test    # Upload to TestPyPI
make upload         # Upload to PyPI
```

### Project Structure
```
my-cli-utilities/
├── account_pool_cli/           # Account Pool CLI
├── device_spy_cli/             # Device Spy CLI  
├── my_cli_utilities_common/    # Shared utilities
│   ├── http_helpers.py         # HTTP request helpers
│   └── pagination.py           # Pagination utilities
├── .cursor/                    # Coding rules and patterns
├── pyproject.toml              # Project configuration
├── Makefile                    # Build automation
└── README.md                   # This file
```

## 🔧 Configuration

### Default Settings
- **Account Pool**: Default environment is `webaqaxmn`, brand `1210`
- **Device Spy**: Supports both Android and iOS platforms
- **Pagination**: 5 items per page by default
- **Cache**: Stored in system temp directory

### Environment Variables
No environment variables required - all configuration is built-in with sensible defaults.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding standards in `.cursor/`
4. Test your changes: `make build && make install-dev`
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the help: `ap help` or `ds help`
2. Review the examples in this README
3. Create an issue on the project repository

---

**Happy CLI-ing! 🚀**