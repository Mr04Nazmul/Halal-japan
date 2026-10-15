import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const jsonHeaders = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
};
const respond = (body: unknown, status = 200, extra: Record<string,string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { ...jsonHeaders, ...extra } });

function corsHeaders(req: Request): Record<string,string> {
  const origin = req.headers.get("Origin") || "";
  const allowed = origin === "https://mr04nazmul.github.io" || origin === "http://localhost:5173";
  return allowed ? {
    "Access-Control-Allow-Origin": origin,
    "Vary": "Origin",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  } : {};
}

Deno.serve(async (req) => {
  const cors = corsHeaders(req);
  const reply = (body: unknown, status = 200) => respond(body, status, cors);
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: cors });
  }
  if (req.method === "GET") {
    // No paid OpenAI call. Does not expose the secret value.
    return reply({
      service: "jhc-ingredient-ai",
      key_saved_in_runtime: Boolean(Deno.env.get("OPENAI_API_KEY")),
      paid_ai_calls_enabled: Deno.env.get("JHC_AI_ANALYSIS_ENABLED") === "true",
      note: "This health check never contacts OpenAI.",
    });
  }
  if (req.method !== "POST") return reply({ error: "method_not_allowed" }, 405);

  // The gateway additionally requires a valid JWT (verify_jwt = true).
  // A publicly distributable anon key alone does NOT authorize paid AI calls.
  const auth = req.headers.get("Authorization") || "";
  const jwt = auth.match(/^Bearer (.+)$/i)?.[1] || "";
  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const publishables = JSON.parse(Deno.env.get("SUPABASE_PUBLISHABLE_KEYS") || "{}");
  const publicApiKey = Deno.env.get("SUPABASE_ANON_KEY") || publishables.default || "";
  if (!jwt || !supabaseUrl || !publicApiKey) return reply({ error: "unauthorized" }, 401);
  try {
    const userCheck = await fetch(supabaseUrl + "/auth/v1/user", {
      headers: { "Authorization": "Bearer " + jwt, "apikey": publicApiKey },
      signal: AbortSignal.timeout(5000),
    });
    if (!userCheck.ok) return reply({ error: "signed_in_user_required" }, 401);
    const user = await userCheck.json();
    if (!user?.id || user?.is_anonymous === true) return reply({ error: "signed_in_user_required" }, 401);
  } catch {
    return reply({ error: "authentication_unavailable" }, 503);
  }

  // Fail closed until the owner explicitly enables metered requests with
  // JHC_AI_ANALYSIS_ENABLED=true and establishes billing/rate-limit rules.
  if (Deno.env.get("JHC_AI_ANALYSIS_ENABLED") !== "true") {
    return reply({ error: "paid_ai_disabled", message: "Safe standby; no OpenAI request made." }, 503);
  }
  const key = Deno.env.get("OPENAI_API_KEY");
  if (!key) return reply({ error: "missing_server_secret" }, 503);

  if (Number(req.headers.get("Content-Length") || "0") > 6000) return reply({ error: "payload_too_large" }, 413);
  let input: unknown;
  try { input = await req.json(); } catch { return reply({ error: "invalid_json" }, 400); }
  if (!input || typeof input !== "object") return reply({ error: "invalid_input" }, 400);
  const body = input as Record<string, unknown>;
  const ingredients = typeof body.ingredients === "string" ? body.ingredients.trim() : "";
  const name = typeof body.product_name === "string" ? body.product_name.trim() : "";
  const barcode = typeof body.barcode === "string" ? body.barcode.trim() : "";
  if (ingredients.length < 3 || ingredients.length > 1500 || name.length > 120 ||
      (barcode && !/^\d{8,14}$/.test(barcode))) {
    return reply({ error: "invalid_ingredients_or_product_info" }, 400);
  }

  // Screening is advisory, never an automatic halal certification.
  const prompt = "You are a careful Japanese food-label ingredient evidence assistant. Extract only explicitly present ingredient terms. Identify explicit pork/porcine terms, gelatin, cooking alcohol, emulsifier, flavouring and uncertain animal-derived additives when mentioned. If origin/slaughter/process is unknown say it cannot be confirmed. Do NOT infer certification and NEVER say a product is halal solely because pork is absent. Output Bangla explanation and factual evidence only.";
  const format = {
    type: "json_schema", name: "jhc_ingredient_screen",
    strict: true,
    schema: {
      type: "object", additionalProperties: false,
      properties: {
        explicit_pork_terms: { type: "array", items: { type: "string" } },
        uncertain_or_flagged_terms: { type: "array", items: { type: "string" } },
        explanation_bn: { type: "string" },
        needs_manufacturer_confirmation: { type: "boolean" },
      },
      required: ["explicit_pork_terms","uncertain_or_flagged_terms","explanation_bn","needs_manufacturer_confirmation"],
    },
  };
  let upstream: Response;
  try {
    upstream = await fetch("https://api.openai.com/v1/responses", {
      method: "POST",
      headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "gpt-4.1-mini",
        instructions: prompt,
        input: JSON.stringify({ product_name: name, barcode, ingredients }),
        text: { format },
        max_output_tokens: 500,
        store: false,
      }),
      signal: AbortSignal.timeout(18000),
    });
  } catch {
    return reply({ error: "analysis_provider_unreachable" }, 502);
  }
  if (!upstream.ok) {
    // Deliberately do not echo vendor payload or credentials to callers.
    return reply({ error: "analysis_provider_rejected", upstream_status: upstream.status }, 502);
  }
  const response = await upstream.json();
  const outputText = (response.output || [])
    .flatMap((item: { content?: { type?: string; text?: string }[] }) => item.content || [])
    .filter((part: {type?: string}) => part.type === "output_text")
    .map((part: {text?: string}) => part.text || "").join("");
  try {
    const analysis = JSON.parse(outputText);
    return reply({
      barcode: barcode || null,
      product_name: name || null,
      verdict: "needs_review",
      evidence_source: "user_supplied_ingredient_text",
      ai_analysis: analysis,
      notice: "AI ingredient screening only. Current product matching, provenance, ingredient origins and halal certification are unverified.",
    });
  } catch {
    return reply({ error: "analysis_parse_failed" }, 502);
  }
});