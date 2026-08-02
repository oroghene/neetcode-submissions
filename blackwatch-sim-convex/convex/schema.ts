import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // One document per scrubbing host. Health lives on the host doc, so the
  // fleet view and each agent's self-view are plain reactive queries.
  hosts: defineTable({
    hostId: v.string(),
    pop: v.string(),
    capacityGbps: v.number(),
    status: v.union(v.literal("active"), v.literal("draining"), v.literal("rebooting")),
    epoch: v.number(),
    // last health report
    cpuPct: v.optional(v.number()),
    memoryUsedBytes: v.optional(v.number()),
    largestFreeBlockBytes: v.optional(v.number()),
    activeMitigations: v.optional(v.number()),
    lastConfigLoadMs: v.optional(v.number()),
    reportedAt: v.optional(v.number()),
  })
    .index("by_hostId", ["hostId"])
    .index("by_pop", ["pop"]),

  mitigations: defineTable({
    mitigationId: v.string(),
    targetCidr: v.string(),
    action: v.union(v.literal("pass"), v.literal("throttle"), v.literal("drop")),
    rateLimitPps: v.number(),
    version: v.number(),
    active: v.boolean(),
    placedAt: v.number(),
  })
    .index("by_mitigationId", ["mitigationId"])
    .index("by_active", ["active"]),

  // Audit trail written atomically with every orchestrator decision.
  rebootLog: defineTable({
    hostId: v.string(),
    pop: v.string(),
    reason: v.string(),
    decidedAt: v.number(),
  }).index("by_hostId", ["hostId"]),

  // One row per mitigation load on a host; powers propagation-latency metrics.
  loadEvents: defineTable({
    hostId: v.string(),
    mitigationId: v.string(),
    propagationMs: v.number(),
    loadedAt: v.number(),
  }),

  datapathKeys: defineTable({
    hostId: v.string(),
    version: v.number(),
    keyMaterial: v.string(),
    status: v.union(v.literal("active"), v.literal("pending_retirement"), v.literal("retired")),
    rotatedAt: v.number(),
  }).index("by_host_status", ["hostId", "status"]),
});
