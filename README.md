# PubMed Paper Fetcher

A tool for fetching PubMed papers with pharmaceutical or biotech company affiliations.

## Features
- Fetches PubMed paper IDs based on search queries.
- Retrieves detailed information about papers, including authors, titles, and publication dates.
- Exports results to a CSV file.

## Requirements
- Python >= 3.10, < 3.12
- Dependencies: `numpy`, `requests`, `pandas`, `argparse`

## Installation
1. Clone the repository.
2. Navigate to the project directory.
3. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage
Run the script using Poetry:
```bash
poetry run get-papers-list "search_query" -f output.csv
```

### Arguments
- `search_query`: The query to search for in PubMed.
- `-f, --file`: The output CSV filename (default: `results.csv`).
- `-d, --debug`: Enable debug mode for verbose output.

## License
This project is licensed under the MIT License.

