import snowflake.connector
from typing import Any, List, Dict
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class SnowflakeClient:
    def __init__(
        self,
        account: str,
        username: str,
        private_key_path: str,
        private_key_passphrase: str | None,
        warehouse: str,
        database: str,
        schema: str,
        role: str = None
    ):
        # Read and decrypt the private key
        with open(private_key_path, 'rb') as key:
            p_key = serialization.load_pem_private_key(
                key.read(),
                password=private_key_passphrase.encode() if private_key_passphrase else None,
                backend=default_backend()
            )

        # Get the private key in DER format
        p_key_der = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        self.conn = snowflake.connector.connect(
            user=username,
            account=account,
            private_key=p_key_der,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role
        )

    @classmethod
    def from_env(cls) -> "SnowflakeClient":
        """Create a client from environment variables."""
        required_vars = [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PRIVATE_KEY_PATH",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            username=os.getenv("SNOWFLAKE_USER"),
            private_key_path=os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"),
            private_key_passphrase=os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE"),
        )

    def query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and return results as a list of dictionaries."""
        cur = self.conn.cursor(snowflake.connector.DictCursor)
        try:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            return cur.fetchall()
        finally:
            cur.close()

    def __del__(self):
        """Close connection when object is destroyed."""
        if hasattr(self, 'conn'):
            self.conn.close()