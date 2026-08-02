import { internalMutation, mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Metrics, Convex edition. There is no scrape endpoint and no agent-side
// aggregation pipeline: metrics are queries over the same tables the control
// plane already writes, and every subscriber (the dashboard) is pushed fresh
// values the moment an underlying row changes.

export const recordLoad = mutation({
  args: {
    hostId: v.string(),
    mitigationId: v.string(),
    propagationMs: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("loadEvents", { ...args, loadedAt: Date.now() });
  },
});

const FRAG_FLOOR_BYTES = 2 * 1024 ** 3;

export const summary = query({
  args: {},
  handler: async (ctx) => {
    const hosts = await ctx.db.query("hosts").collect();
    const active = await ctx.db
      .query("mitigations")
      .withIndex("by_active", (q) => q.eq("active", true))
      .collect();
    const reboots = await ctx.db.query("rebootLog").collect();
    const loads = await ctx.db.query("loadEvents").order("desc").take(100);

    const now = Date.now();
    const connected = hosts.filter(
      (h) => h.reportedAt && now - h.reportedAt < 10_000,
    ).length;
    const fragmented = hosts.filter(
      (h) => (h.largestFreeBlockBytes ?? Infinity) < FRAG_FLOOR_BYTES,
    ).length;

    const sorted = loads.map((l) => l.propagationMs).sort((a, b) => a - b);
    const pct = (p: number) =>
      sorted.length ? sorted[Math.min(Math.floor((p / 100) * sorted.length), sorted.length - 1)] : null;

    return {
      hostsTotal: hosts.length,
      hostsConnected: connected,
      hostsFragmented: fragmented,
      activeMitigations: active.length,
      totalReboots: reboots.length,
      loadsRecorded: loads.length,
      propagationP50Ms: pct(50),
      propagationP95Ms: pct(95),
    };
  },
});

// Demo/ops helper: reset recorded load metrics.
export const clearLoads = internalMutation({
  args: {},
  handler: async (ctx) => {
    for await (const e of ctx.db.query("loadEvents")) {
      await ctx.db.delete(e._id);
    }
  },
});

export const recentReboots = query({
  args: {},
  handler: async (ctx) =>
    (await ctx.db.query("rebootLog").order("desc").take(8)).map((r) => ({
      hostId: r.hostId,
      pop: r.pop,
      reason: r.reason,
      decidedAt: r.decidedAt,
    })),
});
