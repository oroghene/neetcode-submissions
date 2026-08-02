import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

const http = httpRouter();

http.route({
  path: "/stats",
  method: "GET",
  handler: httpAction(async (ctx) => {
    const stats = await ctx.runQuery(api.submissions.stats, {});
    return new Response(JSON.stringify(stats ?? { accepted: 0, total: 0 }), {
      headers: { "Content-Type": "application/json" },
    });
  }),
});

export default http;
