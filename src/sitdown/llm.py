from enum import Enum
import os
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from tqdm import tqdm

from sitdown.slack import SlackThread

from .linear import Issue, Project


OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")


class Model(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4 = "gpt-4"


llm = ChatOpenAI(
    model=Model.GPT_4O_MINI,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
    temperature=0,
)


def get_issue_summary_chain() -> ChatPromptTemplate:
    issue_summary_template = """\
Please summarize this issue in 1-2 sentences, focusing on the key points, status, important comments, and any updates.
* Keep the link/URL to the issue in the output
* If there are github or slack links, include them in the output

Here is the issue:

{issue}
"""

    issue_summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a technical writer summarizing development issues concisely."),
            ("human", issue_summary_template),
        ]
    )

    return issue_summary_prompt | llm | StrOutputParser()


issue_summary_chain = get_issue_summary_chain()


def get_project_summary_chain() -> ChatPromptTemplate:
    project_summary_template = """\
Please summarize this project in 1-2 sentences, focusing on the goals, status, and any important comments:

{project}
"""

    project_summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a technical writer summarizing development projects concisely."),
            ("human", project_summary_template),
        ]
    )

    return project_summary_prompt | llm | StrOutputParser()


project_summary_chain = get_project_summary_chain()


def get_main_chain() -> ChatPromptTemplate:
    system_template = """\
You are a software engineer who is reporting the status of the projects you're working on from your issues in Linear.
"""

    human_template = """\
Here are the issues with their summaries (note that issues are separated by "----------")
----------
{issues}

Please organize and summarize these issues:
* Group the issues by projects
* Use professional tone but be concise
* Issue group title should be bold
* Use the provided issue summaries to create a cohesive overview
* If an issue has a GitHub pull request attached, please include a link to the PR
* Include a link to the linear issue
* If there are any links, include them in the summary
* Format the output as slack markdown using bulleted list
* Output only the summary, no other text
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("human", human_template),
        ]
    )

    return prompt | llm | StrOutputParser()


main_chain = get_main_chain()


def summarize_single_issue(issue: Issue) -> str:
    """Generate a summary for a issue."""
    return issue_summary_chain.invoke({"issue": issue.to_prompt()})


def summarize_single_project(project: Project) -> str:
    """Generate a summary for a project."""
    return project_summary_chain.invoke({"project": project.to_prompt()})


def generate_summary(issues: List[Issue]) -> str:
    """Generate a summary of the issues using LangChain."""
    enhanced_issues = []
    for issue in tqdm(issues, desc="Summarizing issues"):
        summary = summarize_single_issue(issue)
        enhanced_issues.append(f"Title: {issue.title}\nSummary: {summary}")

    issues_text = "\n".join(enhanced_issues)

    print("Generating final summary...")
    response = main_chain.invoke(
        {
            "issues": issues_text,
            # "projects": projects_text,
        }
    )

    return response


def get_slack_thread_summary_chain() -> ChatPromptTemplate:
    slack_thread_summary_template = """\
Please summarize this thread in 1-2 sentences, focusing on the key points, status, important comments, and any updates.

Here is the thread:

{thread}
"""
    slack_thread_summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a technical writer summarizing development issues concisely."),
            ("human", slack_thread_summary_template),
        ]
    )
    return slack_thread_summary_prompt | llm | StrOutputParser()

slack_thread_summary_chain = get_slack_thread_summary_chain()

def get_slack_summary_chain() -> ChatPromptTemplate:
    slack_summary_template = """\
Given the following thread summaries, categorize and summarize the threads in bullet points:

{threads}
"""
    slack_summary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a technical writer summarizing development issues concisely."),
            ("human", slack_summary_template),
        ]
    )
    return slack_summary_prompt | llm | StrOutputParser()

slack_summary_chain = get_slack_summary_chain()


def generate_slack_summary(threads: List[SlackThread], my_slack_user_id: str) -> str:
    """Generate a summary of the threads using LangChain."""
    enhanced_threads = []
    for thread in tqdm(threads, desc="Summarizing threads"):
        summary = slack_thread_summary_chain.invoke({"thread": thread.to_prompt(my_slack_user_id)})
        enhanced_threads.append(f"Thread ID: {thread.thread_id}\nSummary: {summary}")

    threads_text = "----------\n".join(enhanced_threads)

    response = slack_summary_chain.invoke({"threads": threads_text})

    return response
