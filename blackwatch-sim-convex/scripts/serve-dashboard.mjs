// Tiny static server for the dashboard (the dashboard's data never flows
// through here — the page talks straight to the Convex deployment over
// WebSocket).
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "dashboard");
const port = Number(process.env.PORT ?? 8090);
const types = { ".html": "text/html", ".js": "text/javascript", ".map": "application/json" };

createServer(async (req, res) => {
  const path = req.url === "/" ? "/index.html" : req.url.split("?")[0];
  try {
    const body = await readFile(join(root, path));
    res.writeHead(200, { "Content-Type": types[path.slice(path.lastIndexOf("."))] ?? "text/plain" });
    res.end(body);
  } catch {
    res.writeHead(404).end("not found");
  }
}).listen(port, () => console.log(`dashboard on http://localhost:${port}`));
