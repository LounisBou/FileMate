# FileMate

A Python-based file management tool for organizing and sorting media files into categorized directories. FileMate automatically identifies file types, cleans filenames, and organizes your media library with intelligent pattern recognition.

## Features

- **Automatic File Type Detection**: Identifies movies, TV shows, ebooks, audio files, apps, and more based on file extensions
- **Intelligent Filename Cleaning**: Removes unwanted characters and words from filenames for consistent naming
- **Smart Organization**:
  - Movies: Organized into folders with format "Movie Name (Year)"
  - TV Shows: Organized by show name with season/episode detection (s01e04 format)
  - Other media: Sorted into appropriate type-specific directories
- **Metadata Extraction**: Automatically extracts years, season numbers, and episode numbers from filenames
- **Directory Tree Visualization**: Build and display filesystem tree structures
- **Dry Run Mode**: Preview changes before applying them
- **Configurable**: Customize directory names and cleaning rules via environment variables

## Installation

### Requirements

- Python 3.9 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/lounisbou/FileMate.git
cd FileMate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install additional required packages:
```bash
pip install bigtree python-dotenv pydevmate
```

4. Configure environment variables:
```bash
cp .env-example .env
# Edit .env with your preferred directory names and settings
```

## Configuration

Create a `.env` file in the project root (use `.env-example` as template):

```bash
# Directory names for sorted files
MOVIE_DIR="001-MOVIES"
TVSHOW_DIR="002-TVSHOWS"
EBOOK_DIR="003-EBOOKS"
AUDIO_DIR="004-AUDIO"
APP_DIR="005-APPS"
ANDROID_DIR="006-ANDROID"
SCRIPT_DIR="099-SCRIPTS"

# Cleaning configuration files
CLEAN_WORDS_FILE="clean_words.txt"
CLEAN_CHARACTERS_FILE="clean_chars.txt"
```

### Cleaning Rules

Edit `clean_words.txt` and `clean_chars.txt` to customize which words and characters are removed from filenames during cleaning.

## Usage

### Basic Commands

```bash
# Sort files in a directory
python main.py /path/to/directory --sort

# Preview changes without applying them (dry run)
python main.py /path/to/directory --sort --dry-run

# Sort with verbose output
python main.py /path/to/directory --sort --verbose

# Sort and delete remaining files after sorting
python main.py /path/to/directory --sort --clean

# Build and display directory tree
python main.py /path/to/directory --tree --show-tree

# Show help
python main.py --help
```

### Command-Line Options

- `path`: Path to the directory or file to process (required)
- `--sort`: Sort files into categorized directories
- `--tree`: Build the directory tree structure
- `--show-tree`: Display the directory tree (requires --tree)
- `--clean`: Delete remaining elements after sorting (use with caution)
- `--verbose`: Enable verbose output
- `--dry-run`: Preview changes without applying them
- `--version`: Show program version

## Examples

### Example 1: Sort a download folder

```bash
python main.py ~/Downloads --sort --verbose --dry-run
```

This will preview how FileMate would organize your Downloads folder without making changes.

### Example 2: Organize a media library

```bash
python main.py /media/unsorted --sort --clean
```

This will sort all media files into appropriate directories and remove empty folders after sorting.

### Example 3: View directory structure

```bash
python main.py /media/movies --tree --show-tree
```

This displays a visual tree of the directory structure.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code with Black (line length: 99)
black filemate/

# Sort imports
isort filemate/

# Type checking
mypy filemate/

# Linting
pylint filemate/
flake8 filemate/
```

### Project Structure

```
FileMate/
|-- filemate/              # Main package
|   |-- file_system_node.py       # Abstract base class for files/directories
|   |-- file.py                   # File node implementation
|   |-- directory.py              # Directory node implementation
|   |-- sorter.py                 # Main sorting engine
|   |-- node_name_cleaner.py      # Filename cleaning utilities
|   |-- file_type.py              # File type enumeration
|   |-- file_type_extensions.py  # Extension to type mappings
|-- tests/                 # Test suite
|-- main.py               # Entry point
|-- commandlinehelper.py  # CLI argument parsing
|-- clean_words.txt       # Words to remove from filenames
|-- clean_chars.txt       # Characters to remove from filenames
|-- .env-example          # Environment configuration template
|-- requirements.txt      # Python dependencies
```

## How It Works

1. **File Detection**: FileMate analyzes file extensions to determine the type (movie, TV show, ebook, etc.)
2. **Name Cleaning**: Removes unwanted characters and words based on configuration files
3. **Metadata Extraction**: Identifies years (19xx/20xx) and TV show season/episode patterns (s01e04)
4. **Organization**: Moves files to appropriate directories with cleaned, consistent names
5. **Special Handling**:
   - Movies are placed in folders named "Movie Title (Year)"
   - TV shows are organized by show name with proper season/episode structure

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

LounisBou - lounis.bou@gmail.com

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
