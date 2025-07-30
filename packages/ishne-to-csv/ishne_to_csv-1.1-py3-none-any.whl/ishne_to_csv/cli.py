import argparse
import os
import sys
from .core import ishne_to_csv


def main():
    parser = argparse.ArgumentParser(
        description="Convert ISHNE ECG file to CSV with timestamp in UNIX epoch nanoseconds."
    )
    parser.add_argument("input", help="Input ISHNE file path (.ISHNE)")
    parser.add_argument("-o", "--output", help="Output CSV file path (optional)")
    parser.add_argument("-m", "--metadata", help="Saves JSON Metadata to file (optional)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress console output")

    args = parser.parse_args()


    verbose = not args.quiet

    try:
        ishne_to_csv(
            input_file=args.input,
            output_file=args.output,
            metadata_file=args.metadata,
            verbose=verbose,
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
