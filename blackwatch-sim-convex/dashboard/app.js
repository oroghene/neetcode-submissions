// Reactive fleet dashboard: three query subscriptions, zero polling.
// Bundle with: npx esbuild dashboard/app.js --bundle --format=esm --outfile=dashboard/bundle.js
import { ConvexClient } from "convex/browser";
import { api } from "../convex/_generated/api.js";

const url = new URLSearchParams(location.search).get("url") ?? "http://127.0.0.1:3210";
const client = new ConvexClient(url);

const POOL = 8 * 1024 ** 3;
const FLOOR = 2 * 1024 ** 3;
const fmtMB = (b) => (b / 1024 ** 2).toFixed(0) + " MB";
const $ = (id) => document.getElementById(id);

const touched = () =>
  ($("updated").textContent = "last push " + new Date().toLocaleTimeString());

function tile(label, value, sub) {
  return `<div class="tile"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub ?? ""}</div></div>`;
}

client.onUpdate(api.metrics.summary, {}, (s) => {
  $("tiles").innerHTML =
    tile("Hosts connected", `${s.hostsConnected}<span style="font-size:15px;color:var(--muted)">/${s.hostsTotal}</span>`) +
    tile("Active mitigations", s.activeMitigations) +
    tile("Propagation p50", s.propagationP50Ms === null ? "—" : `${s.propagationP50Ms} ms`, `p95 ${s.propagationP95Ms ?? "—"} ms · last ${s.loadsRecorded} loads`) +
    tile("Fragmented hosts", s.hostsFragmented, "below 2 GB floor") +
    tile("Reboots (total)", s.totalReboots, "orchestrator decisions");
  touched();
});

function statusChip(h) {
  if (h.status === "draining") return ["◐", "var(--warning)", "draining"];
  if (h.heartbeatAgeS !== null && h.heartbeatAgeS > 10) return ["○", "var(--critical)", "stale"];
  if (h.largestFreeBlockMB && h.largestFreeBlockMB * 1024 ** 2 < FLOOR)
    return ["▲", "var(--serious)", "fragmented"];
  return ["●", "var(--good)", h.status];
}

client.onUpdate(api.hosts.fleet, {}, (hosts) => {
  $("rows").innerHTML = hosts
    .map((h) => {
      const [dot, color, label] = statusChip(h);
      const bytes = h.largestFreeBlockMB * 1024 ** 2;
      const pct = Math.min((bytes / POOL) * 100, 100);
      const low = bytes < FLOOR;
      return `<tr>
        <td>${h.hostId}</td><td>${h.pop}</td>
        <td><span class="chip"><span class="dot" style="color:${color}">${dot}</span>${label}</span></td>
        <td>${h.epoch}</td>
        <td>${h.activeMitigations}</td>
        <td><div class="meter" title="${fmtMB(bytes)} largest contiguous free block">
          <div class="track"><div class="fill${low ? " low" : ""}" style="width:${pct}%"></div>
          <div class="floor" style="left:${(FLOOR / POOL) * 100}%"></div></div>
          <span class="val">${fmtMB(bytes)}</span></div></td>
        <td>${h.heartbeatAgeS === null ? "—" : h.heartbeatAgeS.toFixed(1) + " s ago"}</td>
      </tr>`;
    })
    .join("");
  touched();
});

client.onUpdate(api.metrics.recentReboots, {}, (rows) => {
  $("reboots").innerHTML = rows.length
    ? rows
        .map(
          (r) => `<tr>
            <td>${new Date(r.decidedAt).toLocaleTimeString()}</td>
            <td>${r.hostId}</td><td>${r.pop}</td><td>${r.reason}</td>
          </tr>`,
        )
        .join("")
    : `<tr><td colspan="4" style="color:var(--muted)">no reboots yet</td></tr>`;
  touched();
});
