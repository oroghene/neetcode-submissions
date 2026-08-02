"""Auto-reboot orchestrator.

The judgment layer: decides which scrubbing hosts are unhealthy and whether it
is *safe* to take one down right now. Safety gates before any drain:

  1. Distributed lock per POP — at most one orchestrator instance reboots in a
     POP at a time (DynamoDB conditional-write lease, in-memory for demos).
  2. Capacity gate — never drain if doing so would drop the POP below the
     minimum healthy fraction (a host mid-attack-mitigation is load-bearing).
  3. One host per run — blast radius control; the next run re-evaluates with
     fresh fleet state rather than acting on a stale snapshot.

Unhealthy means any of: stale heartbeat, dataplane memory fragmentation
(largest_free_block below the floor), or sustained CPU saturation.
"""

import argparse
import os
import sys
import time

import grpc

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/gen/python")
import bwsim_pb2 as pb
import bwsim_pb2_grpc as rpc

from locks import DynamoLockStore, MemoryLockStore

HEARTBEAT_STALE_S = 10
FRAG_FLOOR_BYTES = 2 * 1024**3  # 2GB largest free block minimum
CPU_CEILING_PCT = 95.0
MIN_HEALTHY_FRACTION = 0.66
LOCK_LEASE_S = 60


def classify(host, now_ms):
    """Return a reason string if unhealthy, else None."""
    lh = host.last_health
    if not lh.host_id:
        return None  # never reported; give it a grace period
    if (now_ms - lh.reported_at_unix_ms) / 1000 > HEARTBEAT_STALE_S:
        return "stale heartbeat"
    if lh.largest_free_block_bytes < FRAG_FLOOR_BYTES:
        return (
            f"memory fragmentation: largest_free_block="
            f"{lh.largest_free_block_bytes // 1024**2}MB < floor "
            f"{FRAG_FLOOR_BYTES // 1024**2}MB"
        )
    if lh.cpu_pct > CPU_CEILING_PCT:
        return f"cpu saturation ({lh.cpu_pct:.0f}%)"
    return None


def run_once(stub, locks) -> bool:
    now_ms = int(time.time() * 1000)
    fleet = stub.ListFleet(pb.Empty()).hosts

    by_pop = {}
    for h in fleet:
        by_pop.setdefault(h.info.pop, []).append(h)

    for pop, hosts in sorted(by_pop.items()):
        candidates = [
            (h, reason)
            for h in hosts
            if not h.draining and (reason := classify(h, now_ms))
        ]
        if not candidates:
            continue

        # Capacity gate: only drain if the POP stays above the healthy floor.
        healthy_after = sum(
            1 for h in hosts if h.connected and not classify(h, now_ms)
        ) / max(len(hosts), 1)
        victim, reason = candidates[0]
        if healthy_after < MIN_HEALTHY_FRACTION:
            print(
                f"[orchestrator] {pop}: {victim.info.host_id} unhealthy ({reason}) "
                f"but capacity gate holds ({healthy_after:.0%} healthy after drain "
                f"< {MIN_HEALTHY_FRACTION:.0%}); deferring"
            )
            continue

        lock = locks.acquire(f"reboot:{pop}", LOCK_LEASE_S)
        if lock is None:
            print(f"[orchestrator] {pop}: reboot lock held elsewhere; skipping")
            continue
        try:
            print(
                f"[orchestrator] {pop}: draining {victim.info.host_id} "
                f"(reason: {reason}) [fence={lock['fence']}]"
            )
            ack = stub.DrainHost(
                pb.DrainRequest(host_id=victim.info.host_id, reason=reason)
            )
            print(f"[orchestrator] drain ack ok={ack.ok}")
            return True  # one host per run
        finally:
            locks.release(lock)
    print("[orchestrator] fleet healthy, nothing to do")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="localhost:50061")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=15)
    args = ap.parse_args()

    if os.environ.get("LOCK_TABLE"):
        locks = DynamoLockStore(
            os.environ["LOCK_TABLE"], os.environ.get("DDB_ENDPOINT")
        )
    else:
        locks = MemoryLockStore()

    with grpc.insecure_channel(args.target) as channel:
        stub = rpc.MitigationServiceStub(channel)
        while True:
            run_once(stub, locks)
            if args.once:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
