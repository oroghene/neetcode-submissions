import { internalMutation } from "./_generated/server";
import { internal } from "./_generated/api";
import { v } from "convex/values";

// DKGR-style datapath key rotation. Replaces the Lambda + EventBridge +
// DynamoDB-TTL stack: the cron calls rotateAll; retirement of the old key
// after its grace window is a transactionally-scheduled function instead of
// a TTL attribute.

const GRACE_WINDOW_MS = 24 * 60 * 60 * 1000;

export const rotateAll = internalMutation({
  args: {},
  handler: async (ctx) => {
    const hosts = await ctx.db.query("hosts").collect();
    let rotated = 0;
    for (const host of hosts) {
      await rotateOne(ctx, host.hostId);
      rotated++;
    }
    return { rotated };
  },
});

async function rotateOne(ctx: any, hostId: string) {
  const current = await ctx.db
    .query("datapathKeys")
    .withIndex("by_host_status", (q: any) => q.eq("hostId", hostId).eq("status", "active"))
    .unique();
  const version = (current?.version ?? 0) + 1;
  // crypto.getRandomValues is available in the Convex runtime.
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const keyMaterial = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");

  await ctx.db.insert("datapathKeys", {
    hostId,
    version,
    keyMaterial,
    status: "active",
    rotatedAt: Date.now(),
  });
  if (current) {
    await ctx.db.patch(current._id, { status: "pending_retirement" });
    await ctx.scheduler.runAfter(GRACE_WINDOW_MS, internal.keys.retire, { keyId: current._id });
  }
}

export const retire = internalMutation({
  args: { keyId: v.id("datapathKeys") },
  handler: async (ctx, args) => {
    const key = await ctx.db.get(args.keyId);
    if (key?.status === "pending_retirement") {
      await ctx.db.patch(args.keyId, { status: "retired", keyMaterial: "" });
    }
  },
});
