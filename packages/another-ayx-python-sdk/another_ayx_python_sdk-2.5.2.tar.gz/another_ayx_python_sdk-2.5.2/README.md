# Another AYX Python SDK

A powerful Python SDK for Alteryx Plugin Development and Testing. This SDK provides a comprehensive set of tools and utilities to streamline the development, testing, and deployment of Alteryx plugins.

## Features

- Plugin development framework
- Testing harness for Alteryx plugins
- CLI tools for plugin management
- Support for various Alteryx providers
- Comprehensive documentation and examples

## Requirements

- Python 3.8 or higher
- Alteryx Designer (for plugin testing)

## Installation

You can install the SDK using pip:

```bash
pip install another-ayx-python-sdk
```

For development, install with additional development dependencies:

```bash
pip install "another-ayx-python-sdk[dev]"
```

## Quick Start

1. Create a new plugin project:
```bash
another-ayx-python-sdk create-plugin my-plugin
```

2. Develop your plugin using the provided framework
3. Test your plugin using the testing harness
4. Deploy your plugin to Alteryx Designer

## Project Structure

```
another_ayx_python_sdk/
├── assets/         # Static assets and resources
├── cli/           # Command-line interface tools
├── core/          # Core SDK functionality
├── examples/      # Example plugins and usage
├── providers/     # Alteryx provider implementations
└── test_harness/  # Testing framework
```

## Development

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/jupiterbak/another-ayx-python-sdk.git
cd another-ayx-python-sdk
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- Jupiter Bakakeu (jupiter.bakakeu@gmail.com)

## Support

For support, please open an issue on the [GitHub repository](https://github.com/jupiterbak/another-ayx-python-sdk/issues).

