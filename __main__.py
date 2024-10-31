import click
import dotenv
import os
from linear import LinearClient

dotenv.load_dotenv()
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--days", default=7, help="Number of days to look back")
def my_issues(days):
    """Get issues assigned to you from the last N days"""
    if not LINEAR_API_KEY:
        click.echo("Error: LINEAR_API_KEY environment variable not set")
        return

    linear_client = LinearClient(LINEAR_API_KEY)
    issues = linear_client.get_recent_issues()

    # Format and display the results
    try:
        for issue in issues["data"]["viewer"]["assignedIssues"]["nodes"]:
            click.echo(f"\nTitle: {issue['title']}")
            click.echo(f"State: {issue['state']['name']}")
            if issue["project"]:
                click.echo(f"Project: {issue['project']['name']}")
            click.echo(f"Updated: {issue['updatedAt']}")
    except KeyError as e:
        click.echo(f"Error processing response: {e}")
        click.echo(f"Raw response: {issues}")


@cli.command()
def version():
    """Get the CLI version"""
    click.echo("Linear CLI v0.1.0")


if __name__ == "__main__":
    cli()
