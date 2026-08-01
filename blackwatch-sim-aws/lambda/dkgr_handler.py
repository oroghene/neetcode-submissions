"""DKGR-style datapath key rotation, as a scheduled Lambda.

Every run, for every host in the fleet table:
  - mint a new key version and mark it ACTIVE
  - demote the previous ACTIVE key to PENDING_RETIREMENT with a grace window
    (hosts may still be using it until they confirm reload)
  - let DynamoDB TTL reap keys whose grace window has passed

Runs identically under Lambda (handler) and locally (`python dkgr_handler.py
--local`), with an in-memory table standing in for DynamoDB.
"""

import argparse
import json
import os
import secrets
import time

GRACE_WINDOW_S = 24 * 3600


def rotate_host_key(table, host_id: str, now: int) -> dict:
    prev = table.get_item(Key={"host_id": host_id}).get("Item")
    new_version = (int(prev["version"]) + 1) if prev else 1
    new_key = {
        "host_id": host_id,
        "version": new_version,
        "key_material": secrets.token_hex(32),
        "status": "ACTIVE",
        "rotated_at": now,
    }
    table.put_item(Item=new_key)
    if prev:
        table.put_item(
            Item={
                **prev,
                "host_id": f"{host_id}#v{prev['version']}",
                "status": "PENDING_RETIREMENT",
                "expires_at": now + GRACE_WINDOW_S,  # TTL attribute
            }
        )
    return new_key


def handler(event, context):
    import boto3

    table = boto3.resource("dynamodb").Table(os.environ["KEY_TABLE"])
    hosts = event.get("hosts") or _fleet_hosts()
    now = int(time.time())
    rotated = [rotate_host_key(table, h, now)["version"] for h in hosts]
    return {"rotated": len(rotated), "hosts": hosts}


def _fleet_hosts():
    # In the real system this reads the fleet registry; the simulation takes
    # hosts from the invoke payload or falls back to a fixed demo fleet.
    return ["edge-1", "edge-2", "edge-3"]


class _MemoryTable:
    def __init__(self):
        self.rows = {}

    def get_item(self, Key):
        row = self.rows.get(Key["host_id"])
        return {"Item": row} if row else {}

    def put_item(self, Item):
        self.rows[Item["host_id"]] = Item


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    args = ap.parse_args()
    assert args.local, "run with --local (Lambda uses handler())"
    table = _MemoryTable()
    now = int(time.time())
    for _ in range(2):  # two rotation cycles to show retirement flow
        for host in _fleet_hosts():
            key = rotate_host_key(table, host, now)
            print(f"rotated {host} -> v{key['version']}")
    print(json.dumps(
        {k: {kk: vv for kk, vv in v.items() if kk != "key_material"}
         for k, v in table.rows.items()},
        indent=2,
    ))
