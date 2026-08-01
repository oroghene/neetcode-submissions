import { cronJobs } from "convex/server";
import { internal } from "./_generated/api";

const crons = cronJobs();

// The orchestrator is just a cron over an internal mutation.
crons.interval("auto-reboot sweep", { seconds: 15 }, internal.orchestrator.sweep, {});

// DKGR key rotation, daily.
crons.interval("rotate datapath keys", { hours: 24 }, internal.keys.rotateAll, {});

export default crons;
