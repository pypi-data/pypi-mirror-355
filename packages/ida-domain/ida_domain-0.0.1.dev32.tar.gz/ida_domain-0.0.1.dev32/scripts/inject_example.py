#!/usr/bin/env python3
import os

# Read the template README
with open('README_enhanced.md', 'r') as f:
    readme_content = f.read()

# Check if traverse.py exists
if os.path.exists('examples/traverse.py'):
    # Read traverse.py content
    with open('examples/traverse.py', 'r') as f:
        traverse_content = f.read()

    # Replace placeholder with actual content
    updated_content = readme_content.replace(
        '<!-- TRAVERSE_EXAMPLE_PLACEHOLDER -->', traverse_content
    )
    print('Injected traverse.py content into README')
else:
    # Replace placeholder with error message
    updated_content = readme_content.replace(
        '<!-- TRAVERSE_EXAMPLE_PLACEHOLDER -->', '# Example file not found'
    )
    print('Warning: traverse.py not found, using placeholder')

# Write the updated README
with open('README_enhanced.md', 'w') as f:
    f.write(updated_content)
