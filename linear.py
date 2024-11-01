import dataclasses
import datetime
import requests


@dataclasses.dataclass
class Attachment:
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


@dataclasses.dataclass
class Issue:
    id: str
    title: str
    description: str | None
    updated_at: datetime.datetime
    state: dict[str, str]  # Contains id, name, color, type
    project: dict[str, str]  # Contains id, name
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
            attachments=[
                Attachment.from_json(att)
                for att in data.get("attachments", {}).get("nodes", [])
            ],
        )


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_recent_issues(self):
        url = "https://api.linear.app/graphql"
        headers = {"Authorization": self.api_key}

        query = """
      query {
        viewer {
          assignedIssues(
            filter: {
              updatedAt: { gt: "-P1W" }  # ISO 8601 duration for 1 week ago
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
        response = requests.post(url, headers=headers, json={"query": query})
        data = response.json()
        return [
            Issue.from_json(issue)
            for issue in data["data"]["viewer"]["assignedIssues"]["nodes"]
        ]
