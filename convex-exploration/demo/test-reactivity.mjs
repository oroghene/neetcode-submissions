import { ConvexClient } from "convex/browser";
import { api } from "./convex/_generated/api.js";

const client = new ConvexClient("http://127.0.0.1:3210");
const seen = [];

client.onUpdate(api.submissions.stats, {}, (stats) => {
  seen.push(stats);
  console.log(`[push #${seen.length}]`, JSON.stringify({ accepted: stats?.accepted, total: stats?.total }));
});

await new Promise((r) => setTimeout(r, 1500));
console.log(">> firing mutation: record accepted submission for median-two-sorted");
await client.mutation(api.submissions.record, {
  slug: "median-two-sorted",
  language: "cpp",
  status: "accepted",
  runtimeMs: 95,
});
await new Promise((r) => setTimeout(r, 2500));
console.log(seen.length >= 2 ? "REACTIVITY OK: subscription pushed an update after the mutation" : "NO UPDATE RECEIVED");
await client.close();
process.exit(0);
