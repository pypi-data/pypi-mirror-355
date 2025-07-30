#!/usr/bin/env python3
"""
Database exploration example for IDA Domain API.

This example demonstrates how to open an IDA database and explore its basic properties.
"""

import argparse

import ida_domain


def explore_database(db_path):
    """Explore basic database information."""
    ida_options = ida_domain.IdaCommandBuilder().auto_analysis(True).new_database(True)
    db = ida_domain.Database()
    if db.open(db_path, ida_options):
        # Get basic information
        print(f'Entry point: {hex(db.entry_point)}')
        print(f'Address range: {hex(db.minimum_ea)} - {hex(db.maximum_ea)}')

        # Get metadata
        print('Database metadata:')
        for key, value in db.metadata.items():
            print(f'  {key}: {value}')

        # Count functions
        function_count = 0
        for _ in db.functions.get_all():
            function_count += 1
        print(f'Total functions: {function_count}')

        db.close(save=False)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Database exploration example')
    parser.add_argument(
        '-f', '--input-file', help='Binary input file to be loaded', type=str, required=True
    )
    args = parser.parse_args()
    explore_database(args.input_file)


if __name__ == '__main__':
    main()
