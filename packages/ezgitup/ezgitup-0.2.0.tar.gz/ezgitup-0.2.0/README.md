# EZGitUp

A simple command-line tool to upload files to GitHub repositories.

## Installation

```bash
pip install ezgitup
```

## Usage

### Environment Variables

You can set the following environment variables:
- `GITHUB_TOKEN`: Your GitHub personal access token (required)
- `EZGITUP_DEPO`: Repository in format "owner/repo" or GitHub URL (optional)

The `EZGITUP_DEPO` environment variable supports multiple formats:
- Simple format: `owner/repo`
- SSH URL: `git@github.com:owner/repo.git`
- HTTPS URL: `https://github.com/owner/repo.git`

### Command Line Usage

Upload single or multiple files:

```bash
# Upload single file
ezgitup path/to/file.txt

# Upload multiple files
ezgitup path/to/file1.txt path/to/file2.txt

# Upload files using wildcards
ezgitup *.json                    # All JSON files in current directory
ezgitup path/to/dir/*            # All files in a directory
ezgitup *.py *.json *.md         # Multiple file types
ezgitup test_*.py                # Files matching a pattern

# Specify repository
ezgitup --repo username/repository *.json
# or using short option
ezgitup -r username/repository *.json

# Upload files to a specific directory in the repository
ezgitup --dir docs *.md          # Upload all markdown files to docs/
ezgitup -d src/data *.json       # Upload JSON files to src/data/

# Add UUID to filenames to ensure uniqueness
ezgitup --uuid *.json            # Files will be renamed like: data_a1b2c3d4.json
ezgitup -u *.json                # Same as above, using short option

# Combine options
ezgitup -r username/repository -d docs -u *.md
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

## Requirements

- Python 3.6 or higher
- requests library

## License

Apache-2.0 License

   
