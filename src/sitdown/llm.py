import os
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from tqdm import tqdm

from .linear import Issue
from .template import render


OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Initialize the LLM
llm = ChatOpenAI(
    model="gpt-4",
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    temperature=0,
)

# Define the prompts
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
prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("human", human_template),
])

# Create the chain
chain = prompt | llm | StrOutputParser()

# Create a streaming chain
streaming_chain = (
    {
        "issues": RunnablePassthrough(),
        "projects": RunnablePassthrough(),
    }
    | prompt
    | llm.stream()
    | StrOutputParser()
)

def generate_summary(issues: List[Issue]) -> str:
    """Generate a summary of the issues using LangChain."""
    issues_text = "\n".join(issue.to_prompt() for issue in issues)
    projects = [issue.project for issue in issues if issue.project]
    projects_text = "\n".join(project.to_prompt() for project in projects)

    # Execute the chain
    response = chain.invoke({
        "issues": issues_text,
        "projects": projects_text,
    })

    return response

def generate_summary_streaming(issues: List[Issue]) -> str:
    """Generate a summary of the issues using LangChain with streaming output."""
    issues_text = "\n".join(issue.to_prompt() for issue in issues)
    projects = [issue.project for issue in issues if issue.project]
    projects_text = "\n".join(project.to_prompt() for project in projects)

    result = []
    with tqdm(desc="Generating summary", bar_format="{desc}: {elapsed}") as pbar:
        for chunk in streaming_chain.stream({
            "issues": issues_text,
            "projects": projects_text,
        }):
            result.append(chunk)
            pbar.update(0)  # Updates the spinner

    return "".join(result)
