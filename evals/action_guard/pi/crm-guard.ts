// Pi extension: CRM + finance-warehouse tools backed by the action-guard sandbox server,
// with every call routed through the server's guard gate before execution.
// Requires ACTION_GUARD_URL (e.g. http://127.0.0.1:8781).
import { type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const BASE = process.env.ACTION_GUARD_URL ?? "http://127.0.0.1:8781";

type Spec = { dialect: string; description: string; args: Record<string, string> };

async function post(path: string, body: unknown): Promise<any> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export default async function (pi: ExtensionAPI) {
  const specs: Record<string, Spec> = await (await fetch(`${BASE}/tools`)).json();
  const names = new Set(Object.keys(specs));

  for (const [name, spec] of Object.entries(specs)) {
    const props: Record<string, any> = {};
    for (const [arg, desc] of Object.entries(spec.args)) {
      props[arg] = Type.Optional(Type.Any({ description: desc }));
    }
    pi.registerTool({
      name,
      label: name,
      description: spec.description,
      parameters: Type.Object(props),
      async execute(_id, params) {
        const out = await post("/call", { tool: name, args: params });
        return { content: [{ type: "text", text: JSON.stringify(out) }], details: out };
      },
    });
  }

  // The guard: runs before every tool executes and can block it.
  pi.on("tool_call", async (event) => {
    if (!names.has(event.toolName)) return;
    const verdict = await post("/gate", { tool: event.toolName, args: event.input });
    if (!verdict.allow) return { block: true, reason: `Guard: ${verdict.reason}` };
  });
}
