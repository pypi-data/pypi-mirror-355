#!/usr/bin/env python3
"""
Cross-reference analysis example for IDA Domain API.

This example demonstrates how to analyze cross-references in an IDA database.
"""

import argparse

import ida_domain


def analyze_xrefs(db_path, target_addr):
    """Analyze cross-references to and from a target address."""
    ida_options = ida_domain.IdaCommandBuilder().auto_analysis(True).new_database(True)
    db = ida_domain.Database()
    if db.open(db_path, ida_options):
        print(f'Cross-references to {hex(target_addr)}:')

        # Get references TO the target address
        xref_to_count = 0
        for xref in db.xrefs.get_to(target_addr):
            print(f'  From {hex(xref.frm)} to {hex(xref.to)} (type: {xref.type})')
            xref_to_count += 1

        if xref_to_count == 0:
            print('  No cross-references found')
        else:
            print(f'  Total: {xref_to_count} references')

        print(f'\nCross-references from {hex(target_addr)}:')

        # Get references FROM the target address
        xref_from_count = 0
        for xref in db.xrefs.get_from(target_addr):
            print(f'  From {hex(xref.frm)} to {hex(xref.to)} (type: {xref.type})')
            xref_from_count += 1

        if xref_from_count == 0:
            print('  No outgoing references found')
        else:
            print(f'  Total: {xref_from_count} outgoing references')

        # Summary
        print(f'\nSummary for {hex(target_addr)}:')
        print(f'  Incoming references: {xref_to_count}')
        print(f'  Outgoing references: {xref_from_count}')

        db.close(save=False)


def parse_address(value):
    """Parse address as either decimal or hexadecimal"""
    try:
        if value.lower().startswith('0x'):
            return int(value, 16)
        else:
            return int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError(f'Invalid address format: {value}')


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Database exploration example')
    parser.add_argument(
        '-f', '--input-file', help='Binary input file to be loaded', type=str, required=True
    )
    parser.add_argument(
        '-a',
        '--address',
        help='Address (decimal or hex with 0x prefix)',
        type=parse_address,
        required=True,
    )
    args = parser.parse_args()
    analyze_xrefs(args.input_file, args.address)


if __name__ == '__main__':
    main()
