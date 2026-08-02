import { mutation, query, internalMutation } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

export const record = mutation({
  args: {
    slug: v.string(),
    language: v.string(),
    status: v.union(v.literal("accepted"), v.literal("wrong_answer"), v.literal("tle")),
    runtimeMs: v.number(),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const problem = await ctx.db
      .query("problems")
      .withIndex("by_slug", (q) => q.eq("slug", args.slug))
      .unique();
    if (!problem) throw new Error(`Unknown problem: ${args.slug}`);
    const id = await ctx.db.insert("submissions", {
      problemId: problem._id,
      language: args.language,
      status: args.status,
      runtimeMs: args.runtimeMs,
      notes: args.notes,
    });
    // Transactional scheduling: only fires if this mutation commits.
    await ctx.scheduler.runAfter(0, internal.submissions.rollupStats, {});
    return id;
  },
});

export const rollupStats = internalMutation({
  args: {},
  handler: async (ctx) => {
    const all = await ctx.db.query("submissions").collect();
    const accepted = all.filter((s) => s.status === "accepted").length;
    const day = "today"; // deterministic key for the demo
    const row = await ctx.db
      .query("dailyStats")
      .withIndex("by_day", (q) => q.eq("day", day))
      .unique();
    if (row) {
      await ctx.db.patch(row._id, { accepted, total: all.length });
    } else {
      await ctx.db.insert("dailyStats", { day, accepted, total: all.length });
    }
  },
});

export const recent = query({
  args: { status: v.optional(v.union(v.literal("accepted"), v.literal("wrong_answer"), v.literal("tle"))) },
  handler: async (ctx, args) => {
    const rows = args.status
      ? await ctx.db
          .query("submissions")
          .withIndex("by_status", (q) => q.eq("status", args.status!))
          .order("desc")
          .take(10)
      : await ctx.db.query("submissions").order("desc").take(10);
    return Promise.all(
      rows.map(async (s) => ({
        ...s,
        problem: (await ctx.db.get(s.problemId))?.title,
      })),
    );
  },
});

export const stats = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db
      .query("dailyStats")
      .withIndex("by_day", (q) => q.eq("day", "today"))
      .unique();
  },
});
