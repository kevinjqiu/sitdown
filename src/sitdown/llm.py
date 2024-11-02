from enum import Enum
import os
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .linear import Issue


OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")


class Model(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4 = "gpt-4"


llm = ChatOpenAI(
    model=Model.GPT_4,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    temperature=0,
)

system_template = """
You are a software engineer who is reporting the status of the projects you're working on from your issues in Linear.
"""

human_template = """
Here are the projects I'm working on (separated by "=========="):
==========
{projects}

Here are the issues (note that issues are separated by "----------")
----------
{issues}

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

# Create the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_template),
        ("human", human_template),
    ]
)

chain = prompt | llm | StrOutputParser()


def generate_summary(issues: List[Issue]) -> str:
    """Generate a summary of the issues using LangChain."""
    issues_text = "\n".join(issue.to_prompt() for issue in issues)
    projects = [issue.project for issue in issues if issue.project]
    projects_text = "\n".join(project.to_prompt() for project in projects)

    response = chain.invoke(
        {
            "issues": issues_text,
            "projects": projects_text,
        }
    )

    return response
