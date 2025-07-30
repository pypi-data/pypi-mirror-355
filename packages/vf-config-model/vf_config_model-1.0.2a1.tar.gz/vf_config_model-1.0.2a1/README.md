# Config Model

Shared client configuration models for Verbaflo.

## Installation

```bash
pip install config-model
```

## Usage

```python
from config_model import ClientConfig, WidgetConfig

# Create a new client configuration
config = ClientConfig(
    client_code="example",
    client_name="Example Client",
    # ... other configuration options
)

# Create a widget configuration
widget = WidgetConfig(
    bot_name="Example Bot",
    client_name="Example Client",
    # ... other widget options
)
```

## Features

- Pydantic models for client configuration
- Widget configuration models
- Communication channel configurations
- Feature flag management
- Multi-language support
- And more!

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e .
   ```

## License

MIT License - see [LICENSE](LICENSE) for details. 