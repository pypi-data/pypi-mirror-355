# fujielab-util-launcher

Multiple Program Launcher Utility

[日本語のREADME](README.ja.md)

## Usage

### Command Line Arguments

```
python -m fujielab.util.launcher.run [options]
```
or
```
fujielab-launcher [options]
```

#### Options

- `-d`, `--debug`: Enable debug mode. Detailed log messages will be displayed.
- `--reset-config`: Initialize the configuration file. Existing settings will be overwritten.
- `--version`: Display version information and exit.
- `-h`, `--help`: Display help message and exit.

### Debug Mode

In debug mode, detailed information about the application's operation is displayed.
Detailed logs are output for operations such as saving and loading configuration files,
changing window states, starting and stopping processes, etc.

This is useful for development and troubleshooting. It is not necessary for normal use.

```bash
# Start in debug mode
python -m fujielab.util.launcher.run -d
```

or

```bash
python -m fujielab.util.launcher.run --debug
```

## Features

- Multiple program launcher with configurable settings
- Support for Python scripts and shell commands
- Customizable workspace directory settings
- Cross-platform support (Windows, macOS, Linux)

## Installation

### From PyPI

```bash
pip install fujielab-util-launcher
```

### From Source

```bash
git clone https://github.com/fujielab/fujielab-util-launcher.git
cd fujielab-util-launcher
pip install -e .
```

## License

Apache License 2.0
