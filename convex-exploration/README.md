# Convex Product Exploration

Hands-on exploration of [Convex](https://www.convex.dev)'s product lineup: I ran their
open-source backend locally, built and deployed a real app against it (the demo in
`demo/`), exercised their components ecosystem, and collected thoughtful questions to
ask the team.

---

## 1. The product map

Convex is not one product — it's a stack. Here's the full lineup as of mid-2026:

### Core: the reactive backend (Convex Cloud)
The flagship. A database + serverless TypeScript functions where:
- **Queries are subscriptions.** Every query function is automatically reactive — the
  server tracks each query's read set and pushes updates over WebSocket when any
  underlying data changes. No polling, no cache invalidation code.
- **Mutations are ACID transactions** implemented with optimistic concurrency control
  (OCC). Functions run in a **deterministic V8 runtime** (no raw network/clock access),
  which is what lets Convex safely and automatically retry conflicting transactions.
- **Actions** are the escape hatch for non-deterministic work (calling external APIs,
  LLMs), and they can transactionally schedule mutations.

Platform features bundled in: schema with end-to-end TypeScript types, indexes,
full-text search (BM25), vector search, file storage, a transactional scheduler,
cron jobs, HTTP actions, log streaming, and a very good dashboard.

### Components (~30 first-party building blocks)
Installable backend "sub-apps" — each gets its own sandboxed tables and functions but
participates in the host app's transactions. Notable ones (all `@convex-dev/*` on npm):

| Category | Components |
|---|---|
| Data patterns | `aggregate`, `sharded-counter`, `geospatial`, `migrations`, `table-history`, `prosemirror-sync` |
| Reliability | `workflow` (durable execution), `workpool`, `action-retrier`, `action-cache`, `rate-limiter`, `crons`, `batch-worker` |
| AI | `agent` (+ `agent-playground`), `rag`, `persistent-text-streaming`, durable-agents, `mastra` |
| Integrations | `resend`, `twilio`, `stripe`, `polar`, `launchdarkly`, `expo-push-notifications`, `r2`, `presence`, `static-hosting` |
| Auth | `auth` (Convex Auth), `better-auth`, `workos-authkit` (plus Clerk/Auth0 integrations) |

### AI stack
- **Chef** (chef.convex.dev) — their AI app builder, open-sourced in 2025. Pitch: "the
  only AI app builder that knows backend" — it generates working full-stack apps
  (DB, auth, realtime) because Convex's abstractions are unusually LLM-friendly.
- **Agent component** — persistent threads/memory, RAG, streaming for AI agents stored
  in your database; **durable agents** (async tool loops that survive restarts) are the
  newest addition, built on AI SDK v6.
- **MCP server built into the CLI** (`npx convex mcp start`) — exposes your deployment
  (tables, functions, logs, running queries) to coding agents.

### Open source & self-hosting
- **`get-convex/convex-backend`** — the entire backend, open-sourced (FSL license).
  Ships as a single Rust binary (SQLite by default, also Postgres/MySQL) plus a
  self-hostable dashboard (Docker).
- **Anonymous local dev** — `npx convex dev` can run a fully local deployment without
  an account (there's even a `CONVEX_AGENT_MODE=anonymous` for AI agents).

### Developer tooling
`convex-test` (backend mock for unit tests), ESLint plugin, codemods, `convex-helpers`,
framework bindings (React, Next.js, TanStack, Svelte, Vue, React Native), Python/Rust
clients, a `react-query` adapter, and a Platform API for programmatic project management.

---

## 2. What I actually tried (all against the open-source backend)

Everything below ran in this session against a self-hosted `convex-local-backend`
binary (release `precompiled-2026-07-31`, ~200MB, SQLite storage) — the cloud endpoints
weren't reachable from this sandbox, which turned into a nice accidental test of their
self-hosting story. The demo app is a NeetCode submission tracker (`demo/`).

| Feature | What I did | Result |
|---|---|---|
| Self-host bootstrap | `keygen admin-key` → run binary → point CLI via `CONVEX_SELF_HOSTED_URL` | Zero-to-running in ~2 min; single binary, no services to orchestrate |
| Schema + deploy | 3 tables, 5 indexes incl. a search index | Deployed in ~1s; index diffs printed clearly |
| Mutations + scheduler | `submissions:record` transactionally schedules a stats rollup (`ctx.scheduler.runAfter(0, ...)`) | Rollup ran; scheduling is atomic with the mutation commit |
| Full-text search | `withSearchIndex` BM25 query for "median" | Correct relevance-ranked result |
| HTTP actions | `GET /stats` endpoint on the site proxy (port 3211) | Returned live JSON |
| **Reactivity** | Node client `onUpdate` subscription on a stats query, then fired a mutation | Pushed update arrived in ~1s — and it already included the *cascaded scheduled write*, not just the direct mutation |
| Cron jobs | Hourly rollup cron | Registered and visible |
| Components | `rate-limiter` (token bucket, capacity 3) + `aggregate` (O(log n) count/sum/percentiles) | 4th rapid call rejected with `retryAfter: 16944ms`; median/mean computed without scanning the table |
| Validation | Sent `status: "segfault"` | Crisp `ArgumentValidationError` naming the exact path and validator |
| CLI/tooling | `npx convex data` (table browser), `npx convex logs`, `npx convex mcp` | All worked against the self-hosted instance |

To reproduce: see `demo/` — run the local backend, put `CONVEX_SELF_HOSTED_URL` +
`CONVEX_SELF_HOSTED_ADMIN_KEY` in `.env.local`, then `npx convex dev --once` and
`node test-reactivity.mjs`.

### Honest impressions
- The core loop (edit function → 1s deploy → types flow to client) is genuinely fast,
  and reactivity requiring *zero* extra code is the standout.
- The determinism restrictions (no `fetch`/`Date.now()`-style nondeterminism in
  queries/mutations) are the price of automatic retries and subscriptions — the
  query/mutation/action split is the main new mental model to learn.
- My naive rollup reads the whole submissions table — exactly the anti-pattern that
  causes OCC conflicts at scale, and exactly why the `aggregate`/`sharded-counter`
  components exist. The platform's sharp edges each have a component answering them,
  which is a deliberate strategy worth asking about.
- Components needing an explicit backfill for existing rows shows the migration story
  still has manual steps.

---

## 3. Questions to ask the Convex team

### "Why did you build X?"
1. **The database itself:** You came from building exabyte-scale storage at Dropbox —
   why build a new database with a deterministic runtime instead of layering a sync
   engine on Postgres? What specifically could Postgres never give you — is it the
   read-set tracking for subscriptions, the OCC retry loop, or something else?
2. **Components:** Why design components as sandboxed sub-apps with their own tables
   and functions, rather than plain npm libraries writing to my tables? How do
   transactions and OCC read/write sets work across the component boundary — and what
   does the roadmap item about "reducing component call latency" imply about the
   current cost?
3. **Chef:** Was Chef a product bet in its own right, or a demonstration that Convex's
   abstractions are what LLMs need to generate working backends? What did building it
   teach you that changed the core platform (I saw notes about changing syntax LLMs
   trip on — filters, index syntax)?
4. **The deterministic V8 runtime:** What did you have to give up (Node ecosystem
   compat, the action/mutation split) and would you make the same call today?
5. **Open-sourcing (2025):** After starting cloud-only, what pushed the decision —
   and who actually self-hosts vs. uses the cloud? Is the single-binary local backend
   mostly an adoption funnel or a real deployment target?
6. **The agent/workflow bet:** You wrote "I reimplemented Mastra workflows and I regret
   it" and then shipped durable agents — why is durable agent execution a *database*
   problem rather than a framework problem?

### "What's next?"
7. **Scale ceilings:** The roadmap mentioned moving all backends to new high-scale
   infrastructure and raising function/parallelism limits — where are the current
   ceilings, and what's the largest production workload today?
8. **Local-first / sync:** Your "What is Sync?" essay reads like a manifesto — is a
   client-side persistence / offline / local-first story coming, and how do you think
   about Zero, ElectricSQL, and CRDT-based approaches?
9. **AI-native direction:** The CLI ships an MCP server and anonymous agent mode — do
   you expect AI agents to become the primary "users" of the platform? What's next for
   Chef and the durable-agents component (it's explicitly pre-production today)?
10. **Multi-region/edge and BYO-database:** Self-hosted supports Postgres/MySQL — will
    the cloud ever offer bring-your-own-database or multi-region placement?
11. **Pricing trust:** An early roadmap note said you wanted to "address concerns about
    billing" — what changed, and how do you keep reactive workloads (long-lived
    subscriptions) predictable on usage-based pricing?
12. **Beyond TypeScript:** Clients exist for Python/Rust, but server functions are
    TS-only — is that a permanent identity choice or a temporary constraint?

---

## Sources
- [Convex News – releases](https://news.convex.dev/tag/releases/) · [Open Source Recap 2025](https://news.convex.dev/convex-open-source-recap-2025/) · [Convex raises $24M](https://news.convex.dev/convex-raises-24m/)
- [Meet Convex Chef](https://news.convex.dev/meet-chef/) · [Chef on GitHub](https://github.com/get-convex/chef) · [Lessons from building an AI app builder](https://stack.convex.dev/lessons-from-building-an-ai-app-builder)
- [How Convex Works](https://stack.convex.dev/how-convex-works) · [OCC and Atomicity](https://docs.convex.dev/database/advanced/occ) · [What is Sync?](https://stack.convex.dev/sync)
- [Self-hosting announcement](https://news.convex.dev/self-hosting/) · [convex-backend on GitHub](https://github.com/get-convex/convex-backend)
- [AI Agents docs](https://docs.convex.dev/agents/overview) · [Durable workflows & strong guarantees](https://stack.convex.dev/durable-workflows-and-strong-guarantees) · [I reimplemented Mastra workflows and I regret it](https://stack.convex.dev/reimplementing-mastra-regrets)
- [Forbes on the founders' Dropbox background](https://www.forbes.com/sites/kenrickcai/2022/04/27/convex-series-a-26-million-developers-dump-databases/) · [James Cowling roadmap thread](https://x.com/jamesacowling/status/1887346879043936607)
