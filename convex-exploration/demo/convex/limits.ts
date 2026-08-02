import { RateLimiter, MINUTE } from "@convex-dev/rate-limiter";
import { TableAggregate } from "@convex-dev/aggregate";
import { components } from "./_generated/api";
import { mutation, query } from "./_generated/server";
import { v } from "convex/values";
import { DataModel } from "./_generated/dataModel";

const rateLimiter = new RateLimiter(components.rateLimiter, {
  submitSolution: { kind: "token bucket", rate: 3, period: MINUTE, capacity: 3 },
});

export const runtimeAgg = new TableAggregate<{
  DataModel: DataModel;
  TableName: "submissions";
  Key: number;
}>(components.runtimeStats, {
  sortKey: (doc) => doc.runtimeMs,
  sumValue: (doc) => doc.runtimeMs,
});

export const trySubmit = mutation({
  args: { user: v.string() },
  handler: async (ctx, args) => {
    const { ok, retryAfter } = await rateLimiter.limit(ctx, "submitSolution", {
      key: args.user,
    });
    return { ok, retryAfter };
  },
});

export const backfillAggregate = mutation({
  args: {},
  handler: async (ctx) => {
    for await (const doc of ctx.db.query("submissions")) {
      await runtimeAgg.insertIfDoesNotExist(ctx, doc);
    }
  },
});

export const runtimePercentiles = query({
  args: {},
  handler: async (ctx) => {
    const count = await runtimeAgg.count(ctx);
    if (count === 0) return null;
    const sum = await runtimeAgg.sum(ctx);
    const median = await runtimeAgg.at(ctx, Math.floor(count / 2));
    return { count, meanRuntimeMs: sum / count, medianRuntimeMs: median.key };
  },
});
