import dataclasses
import datetime
import pprint
import requests
import os

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")


@dataclasses.dataclass
class Issue:
    id: str
    title: str
    updated_at: datetime.datetime
    state: str
    project: str


def get_recent_issues():
    url = "https://api.linear.app/graphql"
    headers = {"Authorization": LINEAR_API_KEY}

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


if __name__ == "__main__":
    issues = get_recent_issues()
    pprint.pprint(issues)
