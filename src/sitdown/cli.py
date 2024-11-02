import dotenv

from sitdown.slack import SnowflakeSlackDataSource
from sitdown.snowflake import SnowflakeClient

dotenv.load_dotenv()
import click  # noqa: E402
import os  # noqa: E402

from .linear import LinearClient  # noqa: E402
from .llm import generate_slack_summary, generate_summary  # noqa: E402


LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


@click.group()
def cli():
    pass


@cli.command()
@click.option("--days", default=7, help="Number of days to look back")
def summarize_linear(days):
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


channels = {
    "prj-medusa": "C05EPBHNTUN",
    "eng-roulette": "CSJ6A0PRB",
    "expy": "C7X513PQ8",
}

@cli.command()
@click.option("--days", default=2, help="Number of days to look back")
def summarize_slack(days):
    slack_client = SnowflakeSlackDataSource(SnowflakeClient.from_env())
    user_id = "U01P857JR09"
    channel_ids = list(channels.values())
    threads = slack_client.get_recent_threads(days=days, user_id=user_id, channel_ids=channel_ids)
    click.echo(generate_slack_summary(threads, user_id))


@cli.command()
def version():
    """Get the CLI version"""
    click.echo("sitdown v0.1.0")


if __name__ == "__main__":
    cli()
