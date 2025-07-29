# Shabd

A command-line English dictionary tool for quick word lookups.

## Features

- Lookup English word meanings directly from your terminal
- Caches previously looked up words for offline access
- Simple and straightforward command-line interface

## Installation

You can install Shabd from PyPI:

```bash
pip install shabd
```

Or install directly from the repository:

```bash
git clone https://github.com/spignelon/shabd.git
cd shabd
pip install .
```

## Usage

Basic usage:

```bash
# Look up a single word
shabd apple

# Look up a phrase
shabd "machine learning"
```

Options:

```bash
# Display help
shabd --help

# Display version
shabd --version
```

On first run, Shabd will create a database file `.shabd.db` in your home directory to cache word lookups.

## How It Works

Shabd fetches word definitions from the Cambridge Dictionary website and stores them locally for faster future lookups. The tool stores all looked-up words in a SQLite database located at `~/.shabd.db` in your home directory.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

This project is the continuation of the [cambridge-dictionary](https://github.com/spignelon/cambridge-dictionary) project.