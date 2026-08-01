#!/usr/bin/env bash
# End-to-end demo: control plane + 3 agents (one with a fragmenting dataplane),
# two mitigations placed, then the auto-reboot orchestrator drains the sick host.
set -euo pipefail
cd "$(dirname "$0")/.."

cleanup() { kill $(jobs -p) 2>/dev/null || true; }
trap cleanup EXIT

echo "=== starting control plane ==="
./bin/control-plane -addr :50061 &
sleep 1

echo "=== starting agents (edge-3 simulates memory fragmentation) ==="
python3 agent/agent.py --host-id edge-1 --pop iad-edge-1 &
python3 agent/agent.py --host-id edge-2 --pop iad-edge-1 &
python3 agent/agent.py --host-id edge-3 --pop iad-edge-1 --leak &
sleep 2

echo; echo "=== placing mitigations ==="
python3 ops/opsctl.py place --id mit-001 --cidr 203.0.113.0/24 --action DROP
python3 ops/opsctl.py place --id mit-002 --cidr 198.51.100.0/24 --action THROTTLE --pps 10000
sleep 3

echo; echo "=== fleet before orchestrator ==="
python3 ops/opsctl.py fleet

echo; echo "=== orchestrator run 1 ==="
python3 orchestrator/auto_reboot.py --once
sleep 5

echo; echo "=== fleet after reboot (edge-3 back with reset memory + resynced configs) ==="
python3 ops/opsctl.py fleet

echo; echo "=== orchestrator run 2 (should find fleet healthy) ==="
python3 orchestrator/auto_reboot.py --once

echo; echo "=== DKGR key rotation (local mode) ==="
python3 lambda/dkgr_handler.py --local
echo "DEMO COMPLETE"
