import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

crons.interval("rollup stats hourly", { hours: 1 }, internal.submissions.rollupStats, {});

export default crons;
