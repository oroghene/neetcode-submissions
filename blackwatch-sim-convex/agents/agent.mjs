// Host diagnostics agent, Convex edition.
//
// The gRPC stream + reconnect/backlog machinery from the AWS version is gone:
// the agent subscribes to two reactive queries —
//   - mitigations.active : the full desired config set (push pipeline)
//   - hosts.me           : its own host doc (command channel; a status flip
//                          to "draining" arrives as a push)
// and reports health with a plain mutation. Resync-after-reboot is free:
// the subscription's current value IS the desired state.
import { ConvexClient } from "convex/browser";
import { api } from "../convex/_generated/api.js";

const args = Object.fromEntries(
  process.argv.slice(2).map((a) => a.replace(/^--/, "").split("=")),
);
const HOST_ID = args["host-id"];
const POP = args.pop ?? "iad-edge-1";
const LEAK = "leak" in args;
const URL = process.env.CONVEX_URL ?? "http://127.0.0.1:3310";
const POOL = 8 * 1024 ** 3;

const log = (m) => console.log(`[${HOST_ID}] ${m}`);

const dp = { mitigations: new Map(), wasted: 0 };
const used = () => [...dp.mitigations.values()].reduce((a, b) => a + b, 0) + dp.wasted;
const largestFreeBlock = () =>
  Math.floor(Math.max(POOL - used(), 0) / (1 + dp.mitigations.size / 2));

let lastLoadMs = 0;
let rebooting = false;
let desired = [];
let leaking = LEAK; // a fresh boot clears the fragmentation bug
let resyncing = false;

const client = new ConvexClient(URL);

function loadMitigation(m) {
  const start = Date.now();
  const cost = (200 + Math.floor(Math.random() * 200)) * 1024 ** 2;
  dp.mitigations.set(m.mitigationId, cost);
  if (leaking) dp.wasted += (2000 + Math.floor(Math.random() * 600)) * 1024 ** 2;
  lastLoadMs = Date.now() - start;
  const latency = resyncing
    ? "resync"
    : `propagation=${Date.now() - m.placedAt}ms`;
  log(
    `loaded ${m.mitigationId} action=${m.action} cidr=${m.targetCidr} ` +
      `${latency} largest_free_block=${Math.floor(largestFreeBlock() / 1024 ** 2)}MB`,
  );
}

function syncConfigs(mitigations) {
  desired = mitigations;
  if (rebooting) return;
  for (const m of mitigations) {
    if (!dp.mitigations.has(m.mitigationId)) loadMitigation(m);
  }
  for (const id of dp.mitigations.keys()) {
    if (!mitigations.some((m) => m.mitigationId === id)) {
      dp.mitigations.delete(id);
      log(`unloaded ${id}`);
    }
  }
}

async function reboot(reason) {
  rebooting = true;
  log(`REBOOT commanded (${reason}); draining 2s`);
  await new Promise((r) => setTimeout(r, 2000));
  dp.mitigations.clear();
  dp.wasted = 0;
  leaking = false;
  const epoch = await client.mutation(api.hosts.register, {
    hostId: HOST_ID,
    pop: POP,
    capacityGbps: 100,
  });
  rebooting = false;
  log(`rebooted, memory pool reset; re-registered epoch=${epoch}`);
  resyncing = true;
  syncConfigs(desired); // resync straight from the subscription's value
  resyncing = false;
}

const epoch = await client.mutation(api.hosts.register, {
  hostId: HOST_ID,
  pop: POP,
  capacityGbps: 100,
});
log(`registered, epoch=${epoch}`);

client.onUpdate(api.mitigations.active, {}, syncConfigs);
client.onUpdate(api.hosts.me, { hostId: HOST_ID }, (host) => {
  if (host?.status === "draining" && !rebooting) {
    void reboot("drain requested by orchestrator");
  }
});

setInterval(() => {
  if (rebooting) return;
  void client
    .mutation(api.hosts.heartbeat, {
      hostId: HOST_ID,
      cpuPct: 20 + Math.random() * 40,
      memoryUsedBytes: used(),
      largestFreeBlockBytes: largestFreeBlock(),
      activeMitigations: dp.mitigations.size,
      lastConfigLoadMs: lastLoadMs,
    })
    .catch((e) => log(`heartbeat failed: ${e.message}`));
}, 2000);
