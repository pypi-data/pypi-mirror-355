# Color Zone Processor

A Python tool for processing image color zones by replacing pixels of specific colors with other colors in a structured way.

## Installation

You can install the package using pip:

```bash
pip install .
```

## Usage

After installation, you can use the tool from the command line:

```bash
color-zone-processor --first-percentage 33.53 --total-percentage 33.53
```

### Command Line Arguments

- `--first-percentage`: Percentage of target color pixels to replace with first color (0-100)
- `--total-percentage`: Total percentage of target color pixels to replace (0-100)
- `--min-zone-size`: Minimum size of color zone to consider (default: 100)

### Example

```bash
color-zone-processor --first-percentage 33.53 --total-percentage 33.53 --min-zone-size 100
```

## Development

To install the package in development mode:

```bash
pip install -e .
```

## License

MIT License 