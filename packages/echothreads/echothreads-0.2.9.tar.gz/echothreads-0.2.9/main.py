import os
import subprocess
import yaml
import json
import click
import sys

# Ensure 'echoshell' is importable when running from source
try:
    from echoshell.redis_connector import RedisConnector
except ModuleNotFoundError:
    src_path = os.path.join(os.path.dirname(__file__), "src")
    if os.path.isdir(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)
    from echoshell.redis_connector import RedisConnector

from LoreWeave.parser import LoreWeaveParser

# Path to the echo-scaffold initialization script. The directory is packaged
# with EchoThreads so users can run repository bootstrapping via the CLI.
SCAFFOLD_SCRIPT = os.path.join(os.path.dirname(__file__), "echo-scaffold", "init.py")

@click.group()
def cli():
    """LoreWeave CLI for narrative processing and storage."""
    pass

@click.command()
def init():
    """Initialize LoreWeave configuration and directories."""
    repo_path = os.getcwd()
    config_path = os.path.join(repo_path, "LoreWeave", "config.yaml")
    intention_results_dir = os.path.join(repo_path, "LoreWeave", "intention_results")
    narrative_results_dir = os.path.join(repo_path, "LoreWeave", "narrative_results")
    commit_results_dir = os.path.join(repo_path, "LoreWeave", "commit_results")
    github_issues_dir = os.path.join(repo_path, "LoreWeave", "github_issues")

    os.makedirs(intention_results_dir, exist_ok=True)
    os.makedirs(narrative_results_dir, exist_ok=True)
    os.makedirs(commit_results_dir, exist_ok=True)
    os.makedirs(github_issues_dir, exist_ok=True)

    default_config = {
        "version": "0.1",
        "parser": {
            "glyph_patterns": [
                r"Glyph: ([\w\s]+) \(([^)]+)\)",
                r"([🌀🪶❄️🧩🧠🌸]) ([\w\s]+)"
            ]
        }
    }

    with open(config_path, "w") as f:
        yaml.dump(default_config, f)

    click.echo("LoreWeave initialized with default configuration and directories.")

@click.command(help="Run post-commit and post-push parsing, synchronise GitHub issues and refresh the RedStone registry.\n\nCommit artifacts are stored under `LoreWeave/commit_results`, intentions under `LoreWeave/intention_results`, narrative elements under `LoreWeave/narrative_results` and GitHub issue logs under `LoreWeave/github_issues`. Use --verbose to print each step.")
@click.option('--verbose', is_flag=True, help='Enable verbose output for each processing step.')
@click.option('--issue-limit', default=30, show_default=True, help='Number of GitHub issues to fetch during sync. Set to 0 to skip.')
def run(verbose, issue_limit):
    """Run LoreWeave narrative processing and storage.

    This command performs the following actions:
    1. Post-commit parsing to produce plot points and white feather moments.
    2. Post-push parsing to build narrative fragments and parse commit intentions.
    3. GitHub issue synchronization, writing a summary under ``LoreWeave/github_issues/``.
    4. Intention and narrative extraction saved to ``LoreWeave/intention_results`` and ``LoreWeave/narrative_results``.
    5. RedStone registry refresh to keep local metadata current.
    Parsed fragments are stored in Redis for later retrieval.
    """
    repo_path = os.getcwd()
    config_path = os.path.join(repo_path, "LoreWeave", "config.yaml")
    parser = LoreWeaveParser(repo_path, config_path)

    # Run post-commit processing
    if verbose:
        click.echo('Running post-commit processing...')
    parser.run_post_commit()

    # Run post-push processing
    if verbose:
        click.echo('Running post-push processing...')
    parser.run_post_push()

    # Sync with GitHub issues
    if verbose:
        click.echo('Syncing with GitHub issues...')
    parser.sync_with_github_issues(issue_limit=issue_limit)

    # Update RedStone registry
    if verbose:
        click.echo('Updating RedStone registry...')
    parser.update_redstone_registry()

    # Process and store narrative fragments in Redis
    if verbose:
        click.echo('Storing narrative fragments in Redis...')
    redis_conn = RedisConnector()
    commit_messages = parser.parse_commit_messages_since_last_push()
    for commit in commit_messages:
        parsed_data = parser.parse_commit_message(commit["message"])
        redis_conn.set_key(f"narrative_fragment:{commit['commit_hash']}", json.dumps(parsed_data))

@click.command(help="Initialize a repository using echo-scaffold")
@click.option('--path', default=os.getcwd(), help='Target path for initialization.')
@click.option('--name', default=None, help='Repository name')
@click.option('--anchor', default=None, help='Thread anchor node identifier')
@click.option('--generate-docs', is_flag=True, help='Generate bootstrap documents')
def scaffold(path, name, anchor, generate_docs):
    """Run the echo-scaffold initialization script."""
    # Execute the bundled echo-scaffold tool via its module entry
    cmd = [sys.executable, SCAFFOLD_SCRIPT, '--path', path]
    if name:
        cmd += ['--name', name]
    if anchor:
        cmd += ['--anchor', anchor]
    if generate_docs:
        cmd.append('--generate-docs')
    subprocess.run(cmd)

@click.command(name='devops-test', help='Run recursive DevOps plan tests')
@click.option('--verbose', is_flag=True, help='Verbose test output')
def devops_test(verbose):
    """Execute the recursive_devops_plan_v5 tests."""
    cmd = [sys.executable, '-m', 'unittest', 'recursive_devops_plan_v5_test']
    if verbose:
        cmd.append('-v')
    subprocess.run(cmd)

@click.command()
def help():
    """Show detailed help for LoreWeave commands."""
    click.echo(cli.get_help(click.Context(cli)))

# Add commands to the CLI group
cli.add_command(init)
cli.add_command(run)
cli.add_command(help)
cli.add_command(scaffold)
cli.add_command(devops_test)

if __name__ == "__main__":
    cli()
