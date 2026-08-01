#!/usr/bin/env bash
# End-to-end demo against a local Convex backend (self-hosted or `convex dev`).
# Mirrors blackwatch-sim-aws/scripts/demo.sh step for step.
set -euo pipefail
cd "$(dirname "$0")/.."

cleanup() { kill $(jobs -p) 2>/dev/null || true; }
trap cleanup EXIT

echo "=== building + serving dashboard (http://localhost:8090) ==="
npx esbuild dashboard/app.js --bundle --format=esm --outfile=dashboard/bundle.js --log-level=error
node scripts/serve-dashboard.mjs &

echo "=== starting agents (edge-3 simulates memory fragmentation) ==="
node agents/agent.mjs --host-id=edge-1 --pop=iad-edge-1 &
node agents/agent.mjs --host-id=edge-2 --pop=iad-edge-1 &
node agents/agent.mjs --host-id=edge-3 --pop=iad-edge-1 --leak &
sleep 2

echo; echo "=== placing mitigations (watch propagation= on the agents) ==="
npx convex run mitigations:place '{"mitigationId":"mit-001","targetCidr":"203.0.113.0/24","action":"drop"}'
npx convex run mitigations:place '{"mitigationId":"mit-002","targetCidr":"198.51.100.0/24","action":"throttle","rateLimitPps":10000}'
sleep 3

echo; echo "=== fleet before orchestrator ==="
npx convex run hosts:fleet

echo; echo "=== orchestrator sweep (also runs on a 15s cron) ==="
npx convex run orchestrator:sweep
sleep 5

echo; echo "=== fleet after reboot ==="
npx convex run hosts:fleet

echo; echo "=== sweep again (should be healthy) ==="
npx convex run orchestrator:sweep

echo; echo "=== reboot audit log ==="
npx convex data rebootLog

echo; echo "=== DKGR key rotation ==="
npx convex run keys:rotateAll
npx convex data datapathKeys --limit 6
echo "DEMO COMPLETE"
