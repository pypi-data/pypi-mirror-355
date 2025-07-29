# Aluna CLI

A command-line tool for downloading pathology slide files from the Aluna platform.

## Installation

You can run the CLI directly using `uvx` (no installation required):

```bash
uvx aluna download file1.svs file2.svs
```

Or install it permanently:

```bash
pip install aluna
```

## Usage

### Download SVS files from cart

The recommended way to download files is using a cart ID from the Aluna web interface:

```bash
# Using uvx (recommended)
uvx aluna download --cart YOUR_CART_ID

# If installed
aluna download --cart YOUR_CART_ID
```

To get a cart ID:
1. Visit the Aluna web interface
2. Search for pathology slides
3. Add desired files to your cart
4. Go to the cart page to get your download command with cart ID

### Options

- `--cart`, `-c`: Cart ID from the Aluna web interface
- `--output-dir`, `-o`: Directory to save downloaded files (default: current directory)
- `--parallel`, `-p`: Number of parallel downloads (default: 3)
- `--chunk-size`: Download chunk size in MB (default: 10)
- `--api-url`: Custom API URL (default: https://manaflow-ai--aluna-search-backend-0-serve.modal.run)

### Examples

Download files to a specific directory:

```bash
uvx aluna download --cart YOUR_CART_ID -o ./downloads
```

Download with more parallel connections:

```bash
uvx aluna download --cart YOUR_CART_ID -p 5
```

## Features

- Progress bars for each file download
- Parallel downloads for faster performance
- Automatic retry on failure
- Resume partial downloads
- Checksum verification

## License

MIT License - see LICENSE file for details.