from openai import OpenAI

from .linear import Issue
from .template import render


source = "isc:rpc.medusa.data-eng"
client = OpenAI(
    api_key="unused",
    base_url=f"https://aigateway.instacart.tools/proxy/{source}/openai/v1",
)


SYSTEM_PROMPT = """
You are a helpful assistant that summarizes issues from Linear (a project management tool).
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
* Summarize the issue using the issue's title, description and issue's project's name and description
* If an issue has a GitHub pull request attached, please include a link to the PR in the summary
* Format the output as slack markdown using bullet points
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
