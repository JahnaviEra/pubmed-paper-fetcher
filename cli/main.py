import logging
import argparse
from pubmed_paper_fetcher.pubmed import PubMedFetcher, write_csv, fetch_details_concurrently

def main():
    """
    Main function to fetch PubMed research papers and save the results to a CSV file.
    """
    parser = argparse.ArgumentParser(description="Fetch PubMed research papers.")
    parser.add_argument("query", type=str, help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename.", default="results.csv")
    parser.add_argument("-m", "--max", type=int, help="Maximum number of results to fetch.", default=10)
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    # Configure logging level
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    fetcher = PubMedFetcher(email="your_email@example.com")
    try:
        # Fetch paper IDs
        logging.info(f"Fetching paper IDs for query: {args.query}")
        paper_ids = fetcher.fetch_paper_ids(args.query, max_results=args.max)

        # Fetch paper details concurrently
        logging.info(f"Fetching details for {len(paper_ids)} papers")
        results = fetch_details_concurrently(paper_ids, fetcher)

        # Write results to CSV
        logging.info(f"Writing results to {args.file}")
        write_csv(args.file, results)
        logging.info(f"Results successfully saved to {args.file}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
