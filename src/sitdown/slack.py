import dataclasses
import datetime
import json
from typing import List, Protocol

from sitdown.snowflake import SnowflakeClient


@dataclasses.dataclass(frozen=True)
class SlackMessage:
    id: int
    created_at: datetime.datetime
    slack_id: str
    slack_user_id: str
    content: str

    @classmethod
    def from_dict(cls, data: dict) -> "SlackMessage":
        return cls(
            id=data["id"],
            created_at=data["created_at"],
            slack_id=data["slack_id"],
            slack_user_id=data["slack_user_id"],
            content=data["content"]
        )

    def to_prompt(self, my_slack_user_id: str) -> str:
        if self.slack_user_id == my_slack_user_id:
            return f"**You**\nAt: {self.created_at}\nContent: {self.content}"
        else:
            return f"**{self.slack_user_id}**\nAt: {self.created_at}\nContent: {self.content}"


@dataclasses.dataclass(frozen=True)
class SlackThread:
    thread_id: int
    slack_channel_id: str
    slack_message_id: str
    status: str
    messages: List[SlackMessage]

    @classmethod
    def from_dict(cls, data: dict) -> "SlackThread":
        messages = json.loads(data["MESSAGES"])
        return cls(
            thread_id=data["THREAD_ID"],
            slack_channel_id=data["SLACK_CHANNEL_ID"],
            slack_message_id=data["SLACK_MESSAGE_ID"],
            status=data["STATUS"],
            messages=[SlackMessage.from_dict(m) for m in messages]
        )

    def to_prompt(self, my_slack_user_id: str) -> str:
        messages = [m.to_prompt(my_slack_user_id) for m in self.messages]
        if self.status == "resolved":
            return f"Resolved: Yes\nMessages:\n{messages}"
        return "\n".join(messages)


class SlackDataSource(Protocol):
    def get_recent_threads(self, days: int, user_id: str, channel_ids: list[str]) -> list[SlackThread]:
        """Get messages from the last N days from the given channels for the given user"""
        ...


class SnowflakeSlackDataSource(SlackDataSource):
    def __init__(self, snowflake_client: SnowflakeClient):
        self.snowflake_client = snowflake_client

    def get_recent_threads(self, days: int, user_id: str, channel_ids: list[str]) -> list[dict]:
        query = """
        WITH user_threads AS (
            SELECT DISTINCT t.id as thread_id
            FROM instadata.rds_cheesewiz.threads t
            JOIN instadata.rds_cheesewiz.messages m ON 
                t.slack_channel_id = m.slack_channel_id 
                AND t.slack_message_id = m.slack_thread_id
            WHERE 
                m.created_at >= DATEADD(day, -%(days)s, CURRENT_TIMESTAMP())
                AND m.deleted_at IS NULL
                AND t.deleted_at IS NULL
                AND t.slack_channel_id IN (%(channel_ids)s)
                AND (
                    m.slack_user_id = %(user_id)s
                    OR t.acked_by_slack_user_id = %(user_id)s
                    OR t.resolved_by_slack_user_id = %(user_id)s
                )
        )
        SELECT 
            t.id as thread_id,
            t.slack_channel_id,
            t.slack_message_id,
            t.status,
            t.resolved_at,
            t.acked_at,
            t.resolved_by_slack_user_id,
            t.acked_by_slack_user_id,
            ARRAY_AGG(
                OBJECT_CONSTRUCT(
                    'id', m.id,
                    'created_at', m.created_at,
                    'slack_id', m.slack_id,
                    'slack_user_id', m.slack_user_id,
                    'content', m.content,
                    'important', m.important,
                    'resolution', m.resolution
                )
            ) WITHIN GROUP (ORDER BY m.created_at) as messages
        FROM user_threads ut
        JOIN instadata.rds_cheesewiz.threads t ON t.id = ut.thread_id
        JOIN instadata.rds_cheesewiz.messages m ON 
            t.slack_channel_id = m.slack_channel_id 
            AND t.slack_message_id = m.slack_thread_id
        WHERE m.deleted_at IS NULL
        GROUP BY 
            t.id,
            t.slack_channel_id,
            t.slack_message_id,
            t.status,
            t.resolved_at,
            t.acked_at,
            t.resolved_by_slack_user_id,
            t.acked_by_slack_user_id
        ORDER BY MAX(m.created_at) DESC
        """
        
        results = self.snowflake_client.query(
            query,
            params={
                "days": days,
                "user_id": user_id,
                "channel_ids": channel_ids
            }
        )
        return [SlackThread.from_dict(r) for r in results]
