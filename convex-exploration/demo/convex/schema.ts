import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  problems: defineTable({
    slug: v.string(),
    title: v.string(),
    difficulty: v.union(v.literal("easy"), v.literal("medium"), v.literal("hard")),
    topics: v.array(v.string()),
  })
    .index("by_slug", ["slug"])
    .searchIndex("search_title", { searchField: "title", filterFields: ["difficulty"] }),

  submissions: defineTable({
    problemId: v.id("problems"),
    language: v.string(),
    status: v.union(v.literal("accepted"), v.literal("wrong_answer"), v.literal("tle")),
    runtimeMs: v.number(),
    notes: v.optional(v.string()),
  })
    .index("by_problem", ["problemId"])
    .index("by_status", ["status"]),

  dailyStats: defineTable({
    day: v.string(),
    accepted: v.number(),
    total: v.number(),
  }).index("by_day", ["day"]),
});
