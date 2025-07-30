# Data-Pokemon-VGC

A Python package to download and parse Pokémon VGC tournament data from rk9.gg, including players, pairings, and team details.

## Features

- Download tournament data by tournament code
- Extract players and their teams with detailed Pokémon info
- Save data as JSON files in a structured format
- Command-line interface for easy usage

## Installation

```bash
pip install Data-Pokemon-VGC
```

Or clone the repo and install locally:

```bash
git clone https://github.com/Rxdsilver/Data-Pokemon-VGC.git
cd Data-Pokemon-VGC
pip install .
```

## Usage

Run this script to download tournament:

```bash
python -m scripts.download_tournament 'RK9_Code'
```

Run this script to get usage:

```bash
python -m scripts.compute_usage 'RK9_Code'
```

This will download tournament info, players, pairings, and teams, and save JSON files in the data/ directory named with the tournament code.

## Project Structure

```graphql
├── scripts/
│   └── download_tournament.py   # Main entry point CLI script
├── tournament_parser/
│   ├── models.py                # Data classes for Tournament, Player, Team, etc.
│   ├── parser.py                # Parsing logic from HTML pages
│   ├── utils.py                 # Helper functions (e.g. URL builders)
│   └── save.py                  # Functions to save JSON data
├── data/                       # Output JSON files saved here
├── tests/                      # Unit tests
```

## Development & Tests

- Python 3.11+
- Use `pytest` to run tests

## Continuous Integration

This project uses GitHub Actions for automated bumping version and publishing to PyPI. On every push and pull request, the workflow check commit name to trigger action or not.

Example:

```bash
git commit -m "<some change> bump: patch" # 0.1.2 -> 0.1.3
git commit -m "<some change> bump: minor" # 0.1.2 -> 0.2.0
git commit -m "<some change> bump: major" # 0.1.2 -> 1.0.0
```

