#!/usr/bin/env python3

import os
import sys
import subprocess
from typing import List, Tuple


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def log_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}{message}{Colors.NC}", file=sys.stderr)


def log_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}{message}{Colors.NC}")


def log_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}{message}{Colors.NC}")


def log_info(message: str) -> None:
    """Print info message."""
    print(message)


def validate_parameters() -> Tuple[str, str, List[str], str]:
    """
    Validate required environment variables and return them.

    Returns:
        Tuple of (github_token, github_repo, secret_names, environment)

    Raises:
        SystemExit if validation fails
    """
    github_token = os.environ.get('GITHUB_TOKEN', '')
    github_repo = os.environ.get('GITHUB_REPO', '')
    secret_names_str = os.environ.get('SECRET_NAMES', '')
    environment = os.environ.get('ENVIRONMENT', '')

    if not github_token:
        log_error("Error: GITHUB_TOKEN is required")
        sys.exit(1)

    if not github_repo:
        log_error("Error: GITHUB_REPO is required (format: owner/repo)")
        sys.exit(1)

    if not secret_names_str:
        log_error("Error: SECRET_NAMES is required (comma-separated list)")
        sys.exit(1)

    # Split and clean secret names
    secret_names = [name.strip() for name in secret_names_str.split(',') if name.strip()]

    return github_token, github_repo, secret_names, environment


def set_github_secret(
    secret_name: str,
    secret_value: str,
    repo: str,
    environment: str = None
) -> bool:
    """
    Set a secret in GitHub using gh CLI.

    Args:
        secret_name: Name of the secret
        secret_value: Value of the secret
        repo: GitHub repository in owner/repo format
        environment: Optional GitHub environment name

    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = ['gh', 'secret', 'set', secret_name, '--repo', repo]

        if environment:
            cmd.extend(['--env', environment])

        result = subprocess.run(
            cmd,
            input=secret_value,
            text=True,
            capture_output=True,
            check=False
        )

        if result.returncode != 0:
            log_error(f"    Error: {result.stderr.strip()}")
            return False

        return True
    except Exception as e:
        log_error(f"    Exception: {e}")
        return False


def migrate_secrets(
    secret_names: List[str],
    github_repo: str,
    environment: str = None
) -> Tuple[int, int, int]:
    """
    Migrate secrets from Bitbucket to GitHub.

    Args:
        secret_names: List of secret names to migrate
        github_repo: GitHub repository in owner/repo format
        environment: Optional GitHub environment name

    Returns:
        Tuple of (success_count, failure_count, missing_count)
    """
    success_count = 0
    failure_count = 0
    missing_count = 0

    for secret_name in secret_names:
        log_warning(f"\nProcessing secret: {secret_name}")

        # Get secret value from environment variable
        secret_value = os.environ.get(secret_name, '')

        # GitHub doesn't allow secrets starting with "GITHUB_", so prefix with underscore
        github_secret_name = secret_name
        if secret_name.startswith("GITHUB_"):
            github_secret_name = "_" + secret_name
            log_warning(f"  ⚠ Renaming to '{github_secret_name}' (GitHub reserves GITHUB_ prefix)")

        if not secret_value:
            log_error(f"  ✗ Secret '{secret_name}' not found in Bitbucket pipeline variables")
            missing_count += 1
            continue

        # Set the secret in GitHub
        if environment:
            log_info(f"  → Setting as environment secret in environment: {environment}")
            success = set_github_secret(github_secret_name, secret_value, github_repo, environment)
        else:
            log_info("  → Setting as repository secret")
            success = set_github_secret(github_secret_name, secret_value, github_repo)

        if success:
            log_success(f"  ✓ Successfully set secret: {github_secret_name}")
            success_count += 1
        else:
            log_error(f"  ✗ Failed to set secret: {github_secret_name}")
            failure_count += 1

    return success_count, failure_count, missing_count


def print_summary(success_count: int, failure_count: int, missing_count: int) -> None:
    """Print migration summary."""
    log_success("\n================================")
    log_success("Migration Summary")
    log_success("================================")
    log_success(f"Successfully migrated: {success_count}")
    log_error(f"Failed: {failure_count}")
    log_warning(f"Not found in Bitbucket: {missing_count}")
    log_success("================================")


def main() -> None:
    """Main entry point for the secret migration script."""
    # Enable debug mode if requested
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    if debug:
        log_info("Debug mode enabled")

    # Validate parameters
    # Note: github_token is validated but not used directly - the gh CLI
    # automatically uses the GITHUB_TOKEN environment variable for authentication
    github_token, github_repo, secret_names, environment = validate_parameters()

    # Start migration
    log_success(f"Starting secret migration to GitHub repository: {github_repo}")

    # Migrate secrets
    success_count, failure_count, missing_count = migrate_secrets(
        secret_names,
        github_repo,
        environment
    )

    # Print summary
    print_summary(success_count, failure_count, missing_count)

    # Exit with error if any failures or missing secrets
    if failure_count > 0 or missing_count > 0:
        sys.exit(1)

    log_success("\n✓ All secrets migrated successfully!")


if __name__ == '__main__':
    main()
