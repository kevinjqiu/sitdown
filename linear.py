import dataclasses
import datetime
import requests

from template import render


@dataclasses.dataclass
class Attachment:
    PROMPT_TEMPLATE = """
- {{attachment.title}} ({{attachment.subtitle}}) url: {{attachment.url}}
"""

    url: str
    title: str
    subtitle: str

    @classmethod
    def from_json(cls, data: dict) -> "Attachment":
        return cls(
            url=data["url"],
            title=data["title"],
            subtitle=data["subtitle"],
        )

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)

    def to_prompt(self) -> str:
        return render(self.PROMPT_TEMPLATE, attachment=self)


@dataclasses.dataclass
class Issue:
    PROMPT_TEMPLATE = """
Issue: {{issue.title}}
Description: {{issue.description}}
{% if issue.project %}
Project: {{issue.project.get('name')}}
{% endif %}
{% if issue.state %}
State: {{issue.state.get('name')}}
{% endif %}
Attachments:
{% for att in issue.attachments %}
- {{att.to_prompt()}}
{% endfor %}
----------
"""

    id: str
    title: str
    description: str | None
    updated_at: datetime.datetime
    state: dict[str, str]
    project: dict[str, str]
    attachments: list[Attachment]

    @classmethod
    def from_json(cls, data: dict) -> "Issue":
        updated_at_str = data["updatedAt"].replace("Z", "+00:00")
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            updated_at=datetime.datetime.fromisoformat(updated_at_str),
            state=data["state"],
            project=data["project"],
            attachments=[Attachment.from_json(att) for att in data.get("attachments", {}).get("nodes", [])],
        )

    def to_dict(self) -> dict:
        resp = dataclasses.asdict(self)
        resp["updated_at"] = resp["updated_at"].isoformat()
        resp["attachments"] = [att.to_dict() for att in self.attachments]
        return resp

    def to_prompt(self) -> str:
        return render(self.PROMPT_TEMPLATE, issue=self)


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_recent_issues(self, days: int) -> list[Issue]:
        url = "https://api.linear.app/graphql"
        headers = {"Authorization": self.api_key}

        query = (
            """
      query {
        viewer {
          assignedIssues(
            filter: {
              updatedAt: { gt: "-P%sD" }
            }
          ) {
            nodes {
              id
              title
              description
              updatedAt
              state {
                id
                name
                color
                type
              }
              project {
                id
                name
              }
              attachments {
                nodes {
                  url
                  title
                  subtitle
                }
              }
            }
          }
        }
      }
      """
            % days
        )
        response = requests.post(url, headers=headers, json={"query": query})
        data = response.json()
        return [Issue.from_json(issue) for issue in data["data"]["viewer"]["assignedIssues"]["nodes"]]
