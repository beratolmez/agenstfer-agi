import { execFile } from "node:child_process";
import http from "node:http";
import { promisify } from "node:util";

const exec = promisify(execFile);
const path = process.env.QMD_COLLECTION_PATH || "/knowledge";
const collection = process.env.QMD_COLLECTION_NAME || "company";

async function qmd(args, timeout = 30000) {
  const { stdout } = await exec("qmd", args, { timeout, maxBuffer: 2_000_000 });
  return stdout;
}

async function initialise() {
  try { await qmd(["collection", "add", path, "--name", collection]); } catch {}
  try { await qmd(["update"]); } catch (error) { console.error("qmd update failed", error.message); }
}

const server = http.createServer(async (request, response) => {
  response.setHeader("content-type", "application/json; charset=utf-8");
  if (request.url === "/health") {
    response.end(JSON.stringify({ status: "ok", engine: "qmd" }));
    return;
  }
  if (request.url === "/reindex" && request.method === "POST") {
    try {
      await qmd(["update"], 120000);
      response.end(JSON.stringify({ status: "refreshed", collection }));
    } catch (error) {
      response.statusCode = 503;
      response.end(JSON.stringify({ detail: "qmd reindex failed", reason: error.message }));
    }
    return;
  }
  const url = new URL(request.url, "http://qmd.local");
  if (url.pathname !== "/search") {
    response.statusCode = 404;
    response.end(JSON.stringify({ detail: "not found" }));
    return;
  }
  const query = (url.searchParams.get("q") || "").slice(0, 500);
  const limit = Math.min(Number(url.searchParams.get("limit") || 8), 20);
  try {
    const stdout = await qmd(["search", query, "-c", collection, "--json", "-n", String(limit)]);
    response.end(stdout);
  } catch (error) {
    response.statusCode = 503;
    response.end(JSON.stringify({ detail: "qmd unavailable", reason: error.message }));
  }
});

initialise().finally(() => server.listen(8181, "0.0.0.0"));
