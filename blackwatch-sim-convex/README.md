# blackwatch-sim-convex

The scrubbing-fleet control plane from
[`blackwatch-sim-aws`](../blackwatch-sim-aws) rebuilt on
[Convex](https://convex.dev), replacing as much of the classic stack as possible.
Same simulation, same lifecycle (register → push mitigations → detect fragmentation →
capacity-gated drain → reboot → resync), same demo script — different substrate.

> **Disclaimer:** educational simulation inspired by *public* descriptions of DDoS
> scrubbing architectures. No proprietary code or internal details; the "dataplane"
> is a Map.

## What replaced what

| Concern | AWS-style stack (sibling repo) | Convex version | Delta |
|---|---|---|---|
| Config push pipeline | Go gRPC server-streaming + registry + backlog replay + reconnect handling (~300 lines) | Agents subscribe to the `mitigations.active` **query**; placing a mitigation invalidates it and every host gets pushed the new set | `convex/mitigations.ts` (~30 lines). Resync-after-reboot is the same code path as steady state |
| Command channel (drain/reboot) | Dedicated `RebootCommand` message on the stream + drain bookkeeping | Orchestrator flips `status: "draining"` on the host doc; the agent's subscription to its own doc delivers it | No channel to build at all — it's a field write |
| Distributed lock for reboot safety | DynamoDB conditional-write lease locks + fencing tokens (`orchestrator/locks.py`) | **Gone.** The sweep is one serializable transaction; concurrent sweeps conflict on read/write sets and OCC retries one | The subtlest code in the AWS repo has no Convex equivalent to get wrong |
| Health ingest + fleet view | gRPC `ReportHealth` into server memory (or DynamoDB), consumers poll `ListFleet` | `hosts.heartbeat` mutation; `hosts.fleet` query is *live* for any subscriber (dashboards get realtime for free) | Poll → push |
| Orchestrator process | Long-running Python daemon you deploy and babysit | `crons.interval(15s)` over an internal mutation | No process to operate |
| Key rotation (DKGR) | Lambda + EventBridge schedule + DynamoDB TTL for retirement grace | Cron mutation + `ctx.scheduler.runAfter(grace, retire)` — retirement scheduled transactionally with the rotation | Three services → one function file |
| Audit trail | Would need another table + careful dual-writes | `rebootLog` insert in the same transaction as the drain decision — can never disagree with what happened | Atomicity by default |
| API abuse guard | Custom middleware you'd write | `@convex-dev/rate-limiter` component on `mitigations.place` | Installed, not built |
| Infra definition | CDK stack (3 DynamoDB tables, Lambda, schedule, S3) | `convex/schema.ts` — the schema *is* the infra | No IaC layer |
| Wire contract | `bwsim.proto` + protoc codegen for Go and Python | End-to-end TypeScript types from schema to client | No codegen step |

Measured in the demo: mitigation **propagation ~40-50ms** from operator mutation to
agent load, against the 30-second-class SLA the classic push pipeline is built to.

## What Convex does NOT replace

Honesty section — the parts of the real system that stay exactly where they are:

- **The dataplane.** Line-rate packet scrubbing is C/DPDK on metal; nothing about a
  reactive backend touches that. This repo replaces the *control and ops plane* only.
- **The agent's host-side duties** (loading filters, measuring memory) still need a
  real on-host agent; here it speaks Convex instead of gRPC.
- **Fleet-scale fan-out limits.** Thousands of hosts each holding a subscription is
  exactly Convex's model, but a control plane for 10k+ appliances would need real
  load validation — a good question for the Convex team, not a settled fact.
- **Air-gapped/network-partition behavior.** The gRPC design degrades explicitly;
  here you inherit the Convex client's reconnect semantics.

## Run it

```bash
npm install
# point .env.local at a deployment: either `npx convex dev` (cloud/anonymous local)
# or a self-hosted backend:
#   CONVEX_SELF_HOSTED_URL=http://127.0.0.1:3310
#   CONVEX_SELF_HOSTED_ADMIN_KEY=<from `convex-local-backend keygen admin-key`>
npx convex dev --once   # deploy schema + functions + crons + rate limiter
./scripts/demo.sh
```

Demo output worth noticing:

```
[edge-3] loaded mit-001 action=drop cidr=203.0.113.0/24 propagation=43ms ...
[orchestrator] iad-edge-1: draining edge-3 (memory fragmentation: largest_free_block=1458MB < floor 2048MB)
[edge-3] REBOOT commanded (drain requested by orchestrator); draining 2s
[edge-3] rebooted, memory pool reset; re-registered epoch=4
[edge-3] loaded mit-001 ... resync largest_free_block=5258MB
"fleet healthy, nothing to do"
```

## File map

- `convex/schema.ts` — hosts, mitigations, reboot audit log, datapath keys
- `convex/mitigations.ts` — place/retract + the `active` query that *is* the push pipeline
- `convex/hosts.ts` — register, heartbeat, live fleet view, per-host self view
- `convex/orchestrator.ts` — the auto-reboot sweep as a single transaction (read the
  header comment: why the distributed lock disappeared)
- `convex/keys.ts` — DKGR rotation with scheduler-based retirement
- `convex/crons.ts` — sweep every 15s, rotation daily
- `agents/agent.mjs` — the host agent, subscriptions instead of streams
