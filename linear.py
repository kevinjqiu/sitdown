import dataclasses
import datetime
import requests


@dataclasses.dataclass
class Issue:
    id: str
    title: str
    updated_at: datetime.datetime
    state: str
    project: str


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
            }
          }
        }
      }
      """
        response = requests.post(url, headers=headers, json={"query": query})
        return response.json()
