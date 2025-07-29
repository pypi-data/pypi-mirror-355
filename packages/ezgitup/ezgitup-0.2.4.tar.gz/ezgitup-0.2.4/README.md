# EZGitUp

A simple command-line tool to upload files to GitHub repositories.

## Installation

```bash
pip install ezgitup
```

## Features

- Upload single or multiple files to GitHub repositories
- Support for wildcard patterns (e.g., `*.json`, `test_*.py`)
- Flexible repository specification:
  - Command-line option (`--repo`/`-r`)
  - Simple owner/repo format
  - GitHub SSH URLs
  - GitHub HTTPS URLs
- Target directory support (`--dir`/`-d`)
- UUID support for unique filenames (`--uuid`/`-u`)
- Environment variable configuration
- Interactive mode for user input
- Progress tracking for multiple file uploads
- Version checking

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: Your GitHub personal access token
- `EZGITUP_DEPO`: Default repository (format: owner/repo or full URL)

## Command-line Usage

```bash
# Basic usage
ezgitup file.txt

# Upload multiple files
ezgitup file1.txt file2.txt

# Use wildcards
ezgitup *.txt

# Specify repository
ezgitup -r owner/repo file.txt
# or
ezgitup --repo owner/repo file.txt

# Specify target directory
ezgitup -d docs file.txt
# or
ezgitup --dir docs file.txt

# Add UUID to filenames
ezgitup -u file.txt
# or
ezgitup --uuid file.txt

# Check version
ezgitup --version

# Combined options
ezgitup -r owner/repo -d docs -u *.txt
```

The tool will use the following priority for repository information:
1. Command-line argument (`--repo`/`-r`)
2. Environment variable (`EZGITUP_DEPO`)
3. Interactive prompt

If no files are specified, the tool will prompt you to enter file paths interactively. Wildcards are also supported in interactive mode.

### Interactive Mode

If you don't specify any files or the `EZGITUP_DEPO` environment variable, the tool will guide you through the process:

```bash
ezgitup
```

## Requirements

- Python 3.6 or higher
- `requests` library

## License

Apache-2.0 License