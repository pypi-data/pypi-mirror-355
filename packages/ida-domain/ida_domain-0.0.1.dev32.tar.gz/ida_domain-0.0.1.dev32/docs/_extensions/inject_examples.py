"""
Sphinx extension to replace code placeholders during build without modifying source files.

This extension uses Sphinx's 'source-read' event to modify RST content in memory
during the build process, keeping your working directory clean.
"""

import logging
from pathlib import Path

from sphinx.application import Sphinx

# Set up logger for this extension
logger = logging.getLogger(__name__)


def extract_file(file_path: Path) -> str:
    """Extract entire file content with RST indentation."""
    if not file_path.exists():
        return f'   # Error: {file_path} not found'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f'   # Error reading {file_path}: {e}'

    lines = content.split('\n')

    # Add RST indentation (3 spaces) to each line
    indented_lines = []
    for line in lines:
        if line.startswith('#!'):
            indented_lines.append(line)  # keep shebang unmodified
            continue
        if line.strip():  # Non-empty lines get indented
            indented_lines.append(f'   {line}')
        else:  # Empty lines stay empty
            indented_lines.append('')

    return '\n'.join(indented_lines)


def on_source_read(app: Sphinx, docname: str, source: list) -> None:
    """
    Replace placeholders in RST source during build (in memory only).

    This event is called when Sphinx reads a source file, allowing us to
    modify the content before it's processed, without touching the original file.
    """
    # Only process examples.rst (or any file containing placeholders)
    if docname != 'examples':
        return

    source_dir = Path(app.srcdir)

    # Define placeholder mappings
    replacements = {
        '#EXPLORE_DB_PLACEHOLDER': '../examples/explore_database.py',
        '#ANALYZE_FUNCTIONS_PLACEHOLDER': '../examples/analyze_functions.py',
        '#ANALYZE_STRINGS_PLACEHOLDER': '../examples/analyze_strings.py',
        '#CROSS_REFS_PLACEHOLDER': '../examples/analyze_xrefs.py',
        '#TRAVERSE_PLACEHOLDER': '../examples/traverse.py',
    }

    # Get the source content (source is a list with one string element)
    content = source[0]
    original_content = content

    # Process each replacement
    for placeholder, file_name in replacements.items():
        if placeholder in content:
            python_file = source_dir / file_name
            try:
                replacement_code = extract_file(python_file)
                content = content.replace(placeholder, replacement_code)
                logger.info(f'Replaced {placeholder} with code from {file_name}')
            except Exception as e:
                logger.warning(f'Error replacing {placeholder}: {e}')

    # Update the source content if any replacements were made
    if content != original_content:
        source[0] = content


def setup(app: Sphinx) -> dict:
    """Setup the Sphinx extension."""
    # Connect to the source-read event
    app.connect('source-read', on_source_read)

    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
