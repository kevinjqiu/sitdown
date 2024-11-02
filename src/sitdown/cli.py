import dotenv

dotenv.load_dotenv()
import click  # noqa: E402
import os  # noqa: E402

from .linear import LinearClient  # noqa: E402
from .llm import generate_summary  # noqa: E402


LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--days", default=7, help="Number of days to look back")
def get_summary(days):
    """Get issues assigned to you from the last N days"""
    if not LINEAR_API_KEY:
        click.echo("Error: LINEAR_API_KEY environment variable not set")
        return

    linear_client = LinearClient(LINEAR_API_KEY)
    issues = linear_client.get_recent_issues(days=days)

    try:
        click.echo(f"Found {len(issues)} issues")
    except KeyError as e:
        click.echo(f"Error processing response: {e}")
        click.echo(f"Raw response: {issues}")
        click.echo("Exiting...")
        return

    summary = generate_summary(issues)
    click.echo(summary)


@cli.command()
def version():
    """Get the CLI version"""
    click.echo("sitdown v0.1.0")


if __name__ == "__main__":
    cli()
