// Opt-in local review metadata. No added system prompt or answer coaching.
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export default function (pi: any) {
  const budget = Number(process.env.SAFEGUARD_LAB_BUDGET_USD || "0.5");
  const maxCalls = Number(process.env.SAFEGUARD_LAB_MAX_CALLS || "100");
  function track(ctx: any) {
    const directory = process.env.SAFEGUARD_LAB_RUN_DIR;
    const file = ctx.sessionManager.getSessionFile();
    if (!directory || !file) return;
    const index = join(directory, "session-index.json");
    const files: string[] = existsSync(index) ? JSON.parse(readFileSync(index, "utf8")) : [];
    if (!files.includes(file)) {
      files.push(file);
      writeFileSync(index, JSON.stringify(files, null, 2) + "\n", {mode: 0o600});
    }
  }
  pi.on("session_start", async (_event: any, ctx: any) => track(ctx));
  pi.on("session_shutdown", async (_event: any, ctx: any) => track(ctx));
  function totals(ctx: any) {
    let calls = 0, tokens = 0, cost = 0;
    for (const entry of ctx.sessionManager.getEntries()) {
      const message = entry.type === "message" ? entry.message : undefined;
      if (message?.role === "assistant") calls++;
      const usage = message?.usage || entry.usage;
      if (usage) {
        tokens += Number(usage.totalTokens || 0);
        cost += Number(usage.cost?.total || 0);
      }
    }
    return { calls, tokens, cost };
  }
  function exhausted(ctx: any) {
    const t = totals(ctx);
    return t.calls >= maxCalls || t.cost >= budget;
  }
  function announce(ctx: any) {
    const t = totals(ctx);
    if (ctx.hasUI) ctx.ui.notify(
      `${t.calls} model responses; ${t.tokens} tokens; Pi cost estimate $${t.cost.toFixed(6)}. Billing may differ.`,
      "info");
  }
  pi.registerCommand("feedback", {
    description: "Save a local review note on the last answer; not sent to the model",
    handler: async (note: string, ctx: any) => {
      if (!note.trim()) {
        ctx.ui.notify("Usage: /feedback What was useful, confusing, or incorrect", "info");
        return;
      }
      const last = [...ctx.sessionManager.getBranch()].reverse().find(
        (e: any) => e.type === "message" && e.message?.role === "assistant");
      pi.appendEntry("safeguard-feedback", { note: note.trim(), targetId: last?.id ?? null });
      track(ctx);
      ctx.ui.notify("Feedback saved locally; it was not sent to the model.", "info");
    },
  });
  pi.registerCommand("lab-usage", {
    description: "Show recorded usage for this test session",
    handler: async (_args: string, ctx: any) => announce(ctx),
  });
  pi.on("input", async (_event: any, ctx: any) => {
    if (exhausted(ctx)) {
      if (ctx.hasUI) ctx.ui.notify("Lab request/cost stop reached. Review usage before starting another run.", "warning");
      return { action: "handled" };
    }
    return { action: "continue" };
  });
  pi.on("message_end", async (_event: any, ctx: any) => {
    if (exhausted(ctx)) ctx.abort();
  });
  pi.on("agent_end", async (_event: any, ctx: any) => { track(ctx); announce(ctx); });
}
