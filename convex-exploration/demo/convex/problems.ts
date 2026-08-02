import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
    slug: v.string(),
    title: v.string(),
    difficulty: v.union(v.literal("easy"), v.literal("medium"), v.literal("hard")),
    topics: v.array(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("problems")
      .withIndex("by_slug", (q) => q.eq("slug", args.slug))
      .unique();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return existing._id;
    }
    return await ctx.db.insert("problems", args);
  },
});

export const search = query({
  args: { q: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("problems")
      .withSearchIndex("search_title", (q) => q.search("title", args.q))
      .take(5);
  },
});

export const list = query({
  args: {},
  handler: async (ctx) => ctx.db.query("problems").collect(),
});
