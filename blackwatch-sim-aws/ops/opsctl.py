"""Operator CLI: place mitigations, inspect the fleet, drain hosts."""

import argparse
import sys
import time

import grpc

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/gen/python")
import bwsim_pb2 as pb
import bwsim_pb2_grpc as rpc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="localhost:50061")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("place", help="place a mitigation on the fleet")
    p.add_argument("--id", required=True)
    p.add_argument("--cidr", required=True)
    p.add_argument("--action", choices=["PASS", "THROTTLE", "DROP"], default="DROP")
    p.add_argument("--pps", type=int, default=0)

    sub.add_parser("fleet", help="show fleet status")

    d = sub.add_parser("drain", help="drain and reboot a host")
    d.add_argument("--host-id", required=True)
    d.add_argument("--reason", default="manual drain")

    args = ap.parse_args()
    with grpc.insecure_channel(args.target) as channel:
        stub = rpc.MitigationServiceStub(channel)
        if args.cmd == "place":
            ack = stub.PlaceMitigation(
                pb.PlaceMitigationRequest(
                    config=pb.MitigationConfig(
                        mitigation_id=args.id,
                        target_cidr=args.cidr,
                        action=pb.Action.Value(args.action),
                        rate_limit_pps=args.pps,
                    )
                )
            )
            print(f"place: ok={ack.ok} {ack.message}")
        elif args.cmd == "drain":
            ack = stub.DrainHost(pb.DrainRequest(host_id=args.host_id, reason=args.reason))
            print(f"drain: ok={ack.ok} {ack.message}")
        elif args.cmd == "fleet":
            now_ms = int(time.time() * 1000)
            fleet = stub.ListFleet(pb.Empty())
            for h in sorted(fleet.hosts, key=lambda h: h.info.host_id):
                lh = h.last_health
                age = (now_ms - lh.reported_at_unix_ms) / 1000 if lh.host_id else None
                print(
                    f"{h.info.host_id:12s} pop={h.info.pop:10s} "
                    f"connected={str(h.connected):5s} draining={str(h.draining):5s} "
                    f"mitigations={lh.active_mitigations:2d} "
                    f"largest_free_block={lh.largest_free_block_bytes // 1024**2:5d}MB "
                    f"heartbeat_age={f'{age:.1f}s' if age is not None else 'never'}"
                )


if __name__ == "__main__":
    main()
