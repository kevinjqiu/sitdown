import os

from openai import OpenAI

from .linear import Issue
from .template import render


OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")


kwargs = dict(api_key=OPENAI_API_KEY)
if OPENAI_BASE_URL:
    kwargs["base_url"] = OPENAI_BASE_URL


client = OpenAI(**kwargs)


SYSTEM_PROMPT = """
You are a software engineer who is reporting the status of the projects you're working on from your issues in Linear.
"""

PROMPT_TEMPLATE = """
Here are the projects I'm working on (separated by "=========="):
==========
{{projects}}

Here are the issues (note that issues are separated by "----------")
----------
{{issues}}

Please summarize the issues:
* Group the issues by project
* Use professional tone
* Issue group title should be bold
* Summarize the issue using the issue's title, description and issue's project's name and description
* If an issue doesn't have a description, skip the description part but summarize the issue title
* If an issue has a GitHub pull request attached, please include a link to the PR in the summary
* Format the output as slack markdown using bulleted list
* Output only the summary, no other text
"""


def generate_summary(issues: list[Issue]) -> str:
    issues_text = "\n".join(issue.to_prompt() for issue in issues)

    projects = [issue.project for issue in issues if issue.project]
    projects_text = "\n".join(project.to_prompt() for project in projects)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render(PROMPT_TEMPLATE, issues=issues_text, projects=projects_text)},
        ],
    )

    return response.choices[0].message.content
