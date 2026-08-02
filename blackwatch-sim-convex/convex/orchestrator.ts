import { internalMutation } from "./_generated/server";

// Auto-reboot sweep. The entire decision — read fleet state, classify,
// capacity-gate, pick a victim, mark it draining, write the audit log — is
// ONE serializable transaction. There is no distributed lock: two concurrent
// sweeps conflict on their read/write sets and OCC retries one of them, so
// "at most one drain decision per POP at a time" holds by construction.
//
// Compare orchestrator/locks.py + auto_reboot.py in blackwatch-sim-aws.

const HEARTBEAT_STALE_S = 10;
const FRAG_FLOOR_BYTES = 2 * 1024 ** 3;
const CPU_CEILING_PCT = 95;
const MIN_HEALTHY_FRACTION = 0.66;

type Host = {
  status: string;
  cpuPct?: number;
  largestFreeBlockBytes?: number;
  reportedAt?: number;
};

function classify(h: Host, now: number): string | null {
  if (h.reportedAt === undefined) return null; // grace period: never reported
  if ((now - h.reportedAt) / 1000 > HEARTBEAT_STALE_S) return "stale heartbeat";
  if ((h.largestFreeBlockBytes ?? Infinity) < FRAG_FLOOR_BYTES)
    return `memory fragmentation: largest_free_block=${Math.floor(
      (h.largestFreeBlockBytes ?? 0) / 1024 ** 2,
    )}MB < floor ${FRAG_FLOOR_BYTES / 1024 ** 2}MB`;
  if ((h.cpuPct ?? 0) > CPU_CEILING_PCT) return `cpu saturation (${h.cpuPct}%)`;
  return null;
}

export const sweep = internalMutation({
  args: {},
  handler: async (ctx) => {
    const now = Date.now();
    const hosts = await ctx.db.query("hosts").collect();

    const byPop = new Map<string, typeof hosts>();
    for (const h of hosts) {
      byPop.set(h.pop, [...(byPop.get(h.pop) ?? []), h]);
    }

    const decisions: string[] = [];
    for (const [pop, popHosts] of byPop) {
      const candidates = popHosts
        .filter((h) => h.status === "active")
        .map((h) => ({ h, reason: classify(h, now) }))
        .filter((c): c is { h: (typeof popHosts)[0]; reason: string } => c.reason !== null);
      if (candidates.length === 0) continue;

      const healthyAfter =
        popHosts.filter((h) => h.status === "active" && classify(h, now) === null).length /
        Math.max(popHosts.length, 1);
      const { h: victim, reason } = candidates[0];
      if (healthyAfter < MIN_HEALTHY_FRACTION) {
        decisions.push(`${pop}: ${victim.hostId} unhealthy (${reason}) but capacity gate holds; deferred`);
        continue;
      }

      // Drain decision + audit log commit atomically; the agent learns via
      // its reactive subscription on hosts.me.
      await ctx.db.patch(victim._id, { status: "draining" });
      await ctx.db.insert("rebootLog", { hostId: victim.hostId, pop, reason, decidedAt: now });
      decisions.push(`${pop}: draining ${victim.hostId} (${reason})`);
      // One host per sweep: blast-radius control, same as the AWS version.
      break;
    }
    return decisions.length ? decisions : ["fleet healthy, nothing to do"];
  },
});
