import { mutation, query } from "./_generated/server";
import { v } from "convex/values";
import { RateLimiter, MINUTE } from "@convex-dev/rate-limiter";
import { components } from "./_generated/api";

// Guard the operator API against runaway automation.
const limiter = new RateLimiter(components.rateLimiter, {
  placeMitigation: { kind: "token bucket", rate: 30, period: MINUTE, capacity: 10 },
});

export const place = mutation({
  args: {
    mitigationId: v.string(),
    targetCidr: v.string(),
    action: v.union(v.literal("pass"), v.literal("throttle"), v.literal("drop")),
    rateLimitPps: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    await limiter.limit(ctx, "placeMitigation", { throws: true });
    const latest = await ctx.db.query("mitigations").order("desc").first();
    const version = (latest?.version ?? 0) + 1;
    const existing = await ctx.db
      .query("mitigations")
      .withIndex("by_mitigationId", (q) => q.eq("mitigationId", args.mitigationId))
      .unique();
    const doc = {
      mitigationId: args.mitigationId,
      targetCidr: args.targetCidr,
      action: args.action,
      rateLimitPps: args.rateLimitPps ?? 0,
      version,
      active: true,
      placedAt: Date.now(),
    };
    if (existing) await ctx.db.replace(existing._id, doc);
    else await ctx.db.insert("mitigations", doc);
    return version;
  },
});

export const retract = mutation({
  args: { mitigationId: v.string() },
  handler: async (ctx, args) => {
    const m = await ctx.db
      .query("mitigations")
      .withIndex("by_mitigationId", (q) => q.eq("mitigationId", args.mitigationId))
      .unique();
    if (m) await ctx.db.patch(m._id, { active: false });
  },
});

// THE push pipeline. Every agent subscribes to this query; placing a
// mitigation invalidates it and the new config set is pushed to every
// connected host. Reconnect resync is the same code path: the subscription's
// first result is the full active set.
export const active = query({
  args: {},
  handler: async (ctx) =>
    await ctx.db
      .query("mitigations")
      .withIndex("by_active", (q) => q.eq("active", true))
      .collect(),
});
