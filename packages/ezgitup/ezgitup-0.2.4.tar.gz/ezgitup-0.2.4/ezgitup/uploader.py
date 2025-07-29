#!/usr/bin/env python3
import os
import base64
import requests
import argparse
import glob
import uuid
import sys
import json
from typing import List, Optional, Tuple
from pathlib import Path

try:
    from importlib import metadata as importlib_metadata
except ImportError:
    import importlib_metadata

try:
    __version__ = importlib_metadata.version("ezgitup")
except importlib_metadata.PackageNotFoundError:
    from . import __version__


def get_github_token() -> str:
    """Get GitHub token from environment variable."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError(
            "Please set your GITHUB_TOKEN as an environment variable, i.e. export GITHUB_TOKEN=xxx"
        )
    return token


def get_repo_info() -> Tuple[str, str]:
    """Get repository information from environment variable or user input."""
    repo_info = os.environ.get("EZGITUP_DEPO")
    if repo_info:
        repo_info = repo_info.strip()

        # Handle GitHub URLs
        if repo_info.startswith("git@github.com:"):
            # Remove 'git@github.com:' and '.git' if present
            repo_info = repo_info.replace("git@github.com:", "").replace(".git", "")
        elif repo_info.startswith("https://github.com/"):
            # Remove 'https://github.com/' and '.git' if present
            repo_info = repo_info.replace("https://github.com/", "").replace(".git", "")

        # Try to parse owner/repo from various formats
        parts = repo_info.split("/")
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        elif len(parts) == 1:
            # If only one part is provided, assume it's the repo name
            # and use the current user as the owner
            return os.environ.get("USER", ""), parts[0].strip()
        else:
            # If more than 2 parts, take the last part as repo
            # and everything before the last slash as owner
            owner = "/".join(parts[:-1]).strip()
            repo = parts[-1].strip()
            return owner, repo

    owner = input("Enter the GitHub repository owner (username or organization name): ")
    repo = input("Enter the repository name: ")
    return owner, repo


def get_unique_filename(file_path: str, use_uuid: bool = False) -> str:
    """Get a unique filename, optionally adding UUID."""
    filename = os.path.basename(file_path)
    if not use_uuid:
        return filename

    # Split filename into name and extension
    name, ext = os.path.splitext(filename)
    # Add UUID and return
    return f"{name}_{uuid.uuid4().hex[:8]}{ext}"


def upload_file(
    owner: str,
    repo: str,
    file_path: str,
    token: str,
    target_dir: str = "",
    use_uuid: bool = False,
) -> bool:
    """Upload a single file to GitHub repository."""
    try:
        with open(file_path, "rb") as file:
            content = base64.b64encode(file.read()).decode("utf-8")

        # Get unique filename if requested
        filename = get_unique_filename(file_path, use_uuid)

        # Construct the path in the repository
        repo_path = os.path.join(target_dir, filename).replace("\\", "/").lstrip("/")

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        data = {"message": f"Adding file: {repo_path}", "content": content}

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"Successfully added {repo_path} to the repository!")
            return True
        else:
            error_message = response.json().get("message", "Unknown error")
            print(f"Error uploading {file_path}: {error_message}")
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False


def expand_file_patterns(patterns: List[str]) -> List[str]:
    """Expand wildcard patterns into list of matching files."""
    expanded_files = []
    for pattern in patterns:
        # Expand the pattern
        matches = glob.glob(pattern)
        if not matches:
            print(f"Warning: No files found matching pattern: {pattern}")
        expanded_files.extend(matches)
    return expanded_files


def main():
    parser = argparse.ArgumentParser(description="Upload files to GitHub repository")
    parser.add_argument(
        "files", nargs="*", help="Files to upload (supports wildcards like *.json)"
    )
    parser.add_argument(
        "-r", "--repo", help='GitHub repository in format "owner/repo" or GitHub URL'
    )
    parser.add_argument(
        "-d",
        "--dir",
        help='Target directory in the repository (e.g., "docs" or "src/data")',
    )
    parser.add_argument(
        "-u",
        "--uuid",
        action="store_true",
        help="Add UUID to filenames to ensure uniqueness",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    if args.version:
        print(f"ezgitup version {__version__}")
        sys.exit(0)

    if not args.files:
        parser.print_help()
        sys.exit(1)

    # Get GitHub token
    token = get_github_token()

    # Get repository information
    owner = None
    repo = None

    # If repo provided via CLI, parse it
    if args.repo:
        repo_info = args.repo.strip()

        # Handle GitHub URLs
        if repo_info.startswith("git@github.com:"):
            # Remove 'git@github.com:' and '.git' if present
            repo_info = repo_info.replace("git@github.com:", "").replace(".git", "")
        elif repo_info.startswith("https://github.com/"):
            # Remove 'https://github.com/' and '.git' if present
            repo_info = repo_info.replace("https://github.com/", "").replace(".git", "")

        # Parse owner/repo
        parts = repo_info.split("/")
        if len(parts) == 2:
            owner, repo = parts[0].strip(), parts[1].strip()
        elif len(parts) == 1:
            # If only one part is provided, assume it's the repo name
            # and use the current user as the owner
            owner = os.environ.get("USER", "")
            repo = parts[0].strip()
        else:
            # If more than 2 parts, take the last part as repo
            # and everything before the last slash as owner
            owner = "/".join(parts[:-1]).strip()
            repo = parts[-1].strip()

    # If owner or repo not provided via CLI, try environment variable or prompt
    if not (owner and repo):
        env_owner, env_repo = get_repo_info()
        owner = owner or env_owner
        repo = repo or env_repo

    # Get files to upload
    files_to_upload: List[str] = args.files
    if not files_to_upload:
        while True:
            file_path = input(
                "Enter the path to the file you want to upload (or press Enter to finish): "
            ).strip()
            if not file_path:
                break
            # Expand any wildcards in the input
            matches = glob.glob(file_path)
            if matches:
                files_to_upload.extend(matches)
            else:
                print(f"Warning: No files found matching pattern: {file_path}")

    # Expand any wildcards in the command line arguments
    files_to_upload = expand_file_patterns(files_to_upload)

    if not files_to_upload:
        print("No files specified for upload.")
        return

    # Upload files
    success_count = 0
    total_files = len(files_to_upload)
    for file_path in files_to_upload:
        if upload_file(owner, repo, file_path, token, args.dir, args.uuid):
            success_count += 1

    print(
        f"\nUpload complete: {success_count}/{total_files} files uploaded successfully."
    )
