"""Distributed lease locks over DynamoDB conditional writes.

The real pattern: a lock row per scope (e.g. "reboot:iad-edge-1") acquired
with a conditional PutItem that only succeeds if the row is absent or its
lease has expired. A fencing token (monotonic counter) is returned so a
holder that stalls past its lease can be safely ignored by downstream
consumers.

`MemoryLockStore` implements the same interface for credential-free local
demos; `DynamoLockStore` is the real thing (works against DynamoDB Local via
--endpoint-url too).
"""

import time
import uuid


class LockLost(Exception):
    pass


class MemoryLockStore:
    def __init__(self):
        self._rows = {}

    def acquire(self, scope: str, lease_s: int):
        now = time.time()
        row = self._rows.get(scope)
        if row and row["expires_at"] > now:
            return None
        token = (row["fence"] + 1) if row else 1
        holder = str(uuid.uuid4())
        self._rows[scope] = {
            "holder": holder,
            "expires_at": now + lease_s,
            "fence": token,
        }
        return {"scope": scope, "holder": holder, "fence": token}

    def release(self, lock):
        row = self._rows.get(lock["scope"])
        if row and row["holder"] == lock["holder"]:
            del self._rows[lock["scope"]]


class DynamoLockStore:
    def __init__(self, table_name: str, endpoint_url: str | None = None):
        import boto3

        self._table = boto3.resource("dynamodb", endpoint_url=endpoint_url).Table(
            table_name
        )

    def acquire(self, scope: str, lease_s: int):
        from botocore.exceptions import ClientError

        now = int(time.time())
        holder = str(uuid.uuid4())
        try:
            # Read current fence (best effort) to build the next token.
            current = self._table.get_item(Key={"scope": scope}).get("Item") or {}
            fence = int(current.get("fence", 0)) + 1
            self._table.put_item(
                Item={
                    "scope": scope,
                    "holder": holder,
                    "expires_at": now + lease_s,
                    "fence": fence,
                },
                ConditionExpression=(
                    "attribute_not_exists(#s) OR expires_at < :now"
                ),
                ExpressionAttributeNames={"#s": "scope"},
                ExpressionAttributeValues={":now": now},
            )
            return {"scope": scope, "holder": holder, "fence": fence}
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None  # someone else holds the lease
            raise

    def release(self, lock):
        from botocore.exceptions import ClientError

        try:
            self._table.delete_item(
                Key={"scope": lock["scope"]},
                ConditionExpression="holder = :h",
                ExpressionAttributeValues={":h": lock["holder"]},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise
