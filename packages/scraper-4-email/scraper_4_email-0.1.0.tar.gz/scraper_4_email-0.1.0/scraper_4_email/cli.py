import argparse
from .scraper import run_scraper

def main():
    parser = argparse.ArgumentParser(description="Email scraper from website sitemaps")
    parser.add_argument("input", help="Excel file with ‘site’ column")
    parser.add_argument("output", help="Output CSV file")
    args = parser.parse_args()

    run_scraper(args.input, args.output)
