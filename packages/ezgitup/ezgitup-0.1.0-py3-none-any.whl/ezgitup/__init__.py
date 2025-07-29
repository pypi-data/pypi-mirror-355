#!/usr/bin/env python3
import os
import base64
import requests
import argparse
from typing import List, Optional

def get_github_token() -> str:
    """Get GitHub token from environment variable."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("Please set your GITHUB_TOKEN as an environment variable, i.e. export GITHUB_TOKEN=xxx")
    return token

def get_repo_info() -> tuple[str, str]:
    """Get repository information from environment variable or user input."""
    repo_info = os.environ.get('EZGITUP_DEPO')
    if repo_info:
        try:
            owner, repo = repo_info.split('/')
            return owner.strip(), repo.strip()
        except ValueError:
            print("Warning: EZGITUP_DEPO format should be 'owner/repo'")
    
    owner = input("Enter the GitHub repository owner (username or organization name): ")
    repo = input("Enter the repository name: ")
    return owner, repo

def upload_file(owner: str, repo: str, file_path: str, token: str) -> bool:
    """Upload a single file to GitHub repository."""
    try:
        with open(file_path, 'rb') as file:
            content = base64.b64encode(file.read()).decode('utf-8')

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{os.path.basename(file_path)}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"Adding file: {os.path.basename(file_path)}",
            "content": content
        }

        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"Successfully added {os.path.basename(file_path)} to the repository!")
            return True
        else:
            print(f"Error uploading {file_path}: {response.json().get('message')}")
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload files to GitHub repository')
    parser.add_argument('files', nargs='*', help='Files to upload')
    args = parser.parse_args()

    # Get GitHub token
    token = get_github_token()
    
    # Get repository information
    owner, repo = get_repo_info()
    
    # Get files to upload
    files_to_upload: List[str] = args.files
    if not files_to_upload:
        while True:
            file_path = input("Enter the path to the file you want to upload (or press Enter to finish): ").strip()
            if not file_path:
                break
            if os.path.exists(file_path):
                files_to_upload.append(file_path)
            else:
                print(f"File not found: {file_path}")

    if not files_to_upload:
        print("No files specified for upload.")
        return

    # Upload files
    success_count = 0
    for file_path in files_to_upload:
        if upload_file(owner, repo, file_path, token):
            success_count += 1

    print(f"\nUpload complete: {success_count}/{len(files_to_upload)} files uploaded successfully.")

if __name__ == "__main__":
    main()

"""EZGitUp - A simple tool to upload files to GitHub repositories."""

from .uploader import main

__version__ = "0.1.0" 