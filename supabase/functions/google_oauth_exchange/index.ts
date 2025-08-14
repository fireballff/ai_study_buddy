import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { encode as b64encode } from "https://deno.land/std@0.168.0/encoding/base64.ts";

async function encryptToken(token: string, key: string): Promise<string> {
  const encoder = new TextEncoder();
  // Derive a 256-bit key from the provided string
  const keyMaterial = await crypto.subtle.digest(
    "SHA-256",
    encoder.encode(key),
  );
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyMaterial,
    { name: "AES-GCM" },
    false,
    ["encrypt"],
  );
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const cipherBuffer = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    cryptoKey,
    encoder.encode(token),
  );
  const cipherBytes = new Uint8Array(cipherBuffer);
  const combined = new Uint8Array(iv.byteLength + cipherBytes.byteLength);
  combined.set(iv, 0);
  combined.set(cipherBytes, iv.byteLength);
  return b64encode(combined);
}

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Not found", { status: 404 });
  }

  try {
    const { code, code_verifier, redirect_uri } = await req.json();
    if (!code || !code_verifier || !redirect_uri) {
      return new Response(
        JSON.stringify({ ok: false, error: "Missing parameters" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const GOOGLE_CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID");
    const GOOGLE_CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET");
    if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET) {
      return new Response(
        JSON.stringify({ ok: false, error: "Server misconfigured" }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      );
    }

    const tokenResp = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        code,
        code_verifier,
        redirect_uri,
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
        grant_type: "authorization_code",
      }),
    });

    if (!tokenResp.ok) {
      const err = await tokenResp.json().catch(() => ({ error: "token exchange failed" }));
      return new Response(
        JSON.stringify({ ok: false, error: err }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const tokenJson = await tokenResp.json();
    const refreshToken = tokenJson.refresh_token as string | undefined;
    if (!refreshToken) {
      return new Response(
        JSON.stringify({ ok: false, error: "No refresh token returned" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
    const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const ENCRYPTION_KEY = Deno.env.get("SYM_ENCRYPTION_KEY") ?? "";
    if (!SUPABASE_URL || !SERVICE_ROLE_KEY || !ENCRYPTION_KEY) {
      return new Response(
        JSON.stringify({ ok: false, error: "Server misconfigured" }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      );
    }

    const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
      auth: { persistSession: false },
    });

    const authHeader = req.headers.get("Authorization") ?? "";
    const jwt = authHeader.replace("Bearer ", "");
    const {
      data: { user },
      error: userErr,
    } = await supabase.auth.getUser(jwt);
    if (userErr || !user) {
      return new Response(
        JSON.stringify({ ok: false, error: "Unauthorized" }),
        { status: 401, headers: { "Content-Type": "application/json" } },
      );
    }

    const cipher = await encryptToken(refreshToken, ENCRYPTION_KEY);

    const { error: upsertErr } = await supabase
      .from("secure_credentials")
      .upsert(
        {
          owner_user_id: user.id,
          provider: "google",
          refresh_token_cipher: cipher,
        },
        { onConflict: "owner_user_id,provider" },
      );

    if (upsertErr) {
      return new Response(
        JSON.stringify({ ok: false, error: upsertErr.message }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    return new Response(
      JSON.stringify({ ok: true }),
      { headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: err.message }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});
