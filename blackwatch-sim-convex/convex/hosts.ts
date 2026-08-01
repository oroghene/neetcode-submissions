import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const register = mutation({
  args: { hostId: v.string(), pop: v.string(), capacityGbps: v.number() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("hosts")
      .withIndex("by_hostId", (q) => q.eq("hostId", args.hostId))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, {
        status: "active",
        epoch: existing.epoch + 1,
        pop: args.pop,
        capacityGbps: args.capacityGbps,
      });
      return existing.epoch + 1;
    }
    await ctx.db.insert("hosts", { ...args, status: "active", epoch: 1 });
    return 1;
  },
});

export const heartbeat = mutation({
  args: {
    hostId: v.string(),
    cpuPct: v.number(),
    memoryUsedBytes: v.number(),
    largestFreeBlockBytes: v.number(),
    activeMitigations: v.number(),
    lastConfigLoadMs: v.number(),
  },
  handler: async (ctx, { hostId, ...health }) => {
    const host = await ctx.db
      .query("hosts")
      .withIndex("by_hostId", (q) => q.eq("hostId", hostId))
      .unique();
    if (!host) throw new Error(`unknown host ${hostId}`);
    await ctx.db.patch(host._id, { ...health, reportedAt: Date.now() });
  },
});

// Each agent subscribes to its own host doc; a status flip to "draining"
// reaches it as a reactive push — no command channel to build.
export const me = query({
  args: { hostId: v.string() },
  handler: async (ctx, args) =>
    await ctx.db
      .query("hosts")
      .withIndex("by_hostId", (q) => q.eq("hostId", args.hostId))
      .unique(),
});

export const fleet = query({
  args: {},
  handler: async (ctx) => {
    const hosts = await ctx.db.query("hosts").collect();
    return hosts
      .sort((a, b) => a.hostId.localeCompare(b.hostId))
      .map((h) => ({
        hostId: h.hostId,
        pop: h.pop,
        status: h.status,
        epoch: h.epoch,
        activeMitigations: h.activeMitigations ?? 0,
        largestFreeBlockMB: Math.floor((h.largestFreeBlockBytes ?? 0) / 1024 ** 2),
        heartbeatAgeS: h.reportedAt ? (Date.now() - h.reportedAt) / 1000 : null,
      }));
  },
});
