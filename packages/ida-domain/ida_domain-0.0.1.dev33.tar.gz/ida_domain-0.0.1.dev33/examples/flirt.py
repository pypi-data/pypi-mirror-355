#!/usr/bin/env python3
"""
Database FLIRT example for IDA Domain API.

This example demonstrates how to work with signature files.
"""

import argparse
import json
from dataclasses import asdict

import ida_domain


def list_flirt_details(db_path):
    ida_options = ida_domain.IdaCommandBuilder().auto_analysis(True).new_database(True)

    db = ida_domain.Database()
    if db.open(db_path, ida_options):
        files = db.flirt.get_files()
        for f in files:
            details = db.flirt.apply(f, probe_only=True)
            for d in details:
                if d.matches > 0:
                    print(json.dumps(asdict(d), indent=4))

        db.close(False)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Database traversing example')
    parser.add_argument(
        '-f', '--input-file', help='Binary input file to be loaded', type=str, required=True
    )
    args = parser.parse_args()
    list_flirt_details(args.input_file)


if __name__ == '__main__':
    main()
