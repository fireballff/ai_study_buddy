import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { encode as b64encode, decode as b64decode } from "https://deno.land/std@0.168.0/encoding/base64.ts";

async function encryptToken(token: string, key: string): Promise<string> {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.digest("SHA-256", encoder.encode(key));
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

async function decryptToken(cipherText: string, key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = b64decode(cipherText);
  const iv = data.slice(0, 12);
  const cipher = data.slice(12);
  const keyMaterial = await crypto.subtle.digest("SHA-256", encoder.encode(key));
  const cryptoKey = await crypto.subtle.importKey(
    "raw",
    keyMaterial,
    { name: "AES-GCM" },
    false,
    ["decrypt"],
  );
  const plainBuffer = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    cryptoKey,
    cipher,
  );
  return new TextDecoder().decode(plainBuffer);
}

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Not found", { status: 404 });
  }

  try {
    const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
    const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    const ENCRYPTION_KEY = Deno.env.get("SYM_ENCRYPTION_KEY") ?? "";
    const GOOGLE_CLIENT_ID = Deno.env.get("GOOGLE_CLIENT_ID") ?? "";
    const GOOGLE_CLIENT_SECRET = Deno.env.get("GOOGLE_CLIENT_SECRET") ?? "";
    if (
      !SUPABASE_URL ||
      !SERVICE_ROLE_KEY ||
      !ENCRYPTION_KEY ||
      !GOOGLE_CLIENT_ID ||
      !GOOGLE_CLIENT_SECRET
    ) {
      return new Response(
        JSON.stringify({ ok: false, error: "Server misconfigured" }),
        { status: 500, headers: { "Content-Type": "application/json" } },
      );
    }

    const authHeader = req.headers.get("Authorization") ?? "";
    const jwt = authHeader.replace("Bearer ", "");

    const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
      auth: { persistSession: false },
    });

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

    const { data: creds, error: credsErr } = await supabase
      .from("secure_credentials")
      .select("refresh_token_cipher")
      .eq("owner_user_id", user.id)
      .eq("provider", "google")
      .single();

    if (credsErr || !creds) {
      return new Response(
        JSON.stringify({ ok: false, error: "No credentials" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const refreshToken = await decryptToken(
      creds.refresh_token_cipher as string,
      ENCRYPTION_KEY,
    );

    const tokenResp = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID,
        client_secret: GOOGLE_CLIENT_SECRET,
        refresh_token: refreshToken,
        grant_type: "refresh_token",
      }),
    });

    if (!tokenResp.ok) {
      const err = await tokenResp.json().catch(() => ({ error: "token mint failed" }));
      return new Response(
        JSON.stringify({ ok: false, error: err }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const tokenJson = await tokenResp.json();
    const accessToken = tokenJson.access_token as string | undefined;
    const expiresIn = tokenJson.expires_in as number | undefined;
    if (!accessToken) {
      return new Response(
        JSON.stringify({ ok: false, error: "No access token" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }

    const newRefresh = tokenJson.refresh_token as string | undefined;
    if (newRefresh) {
      const cipher = await encryptToken(newRefresh, ENCRYPTION_KEY);
      await supabase
        .from("secure_credentials")
        .upsert(
          {
            owner_user_id: user.id,
            provider: "google",
            refresh_token_cipher: cipher,
          },
          { onConflict: "owner_user_id,provider" },
        );
    }

    return new Response(
      JSON.stringify({ access_token: accessToken, expires_in: expiresIn }),
      { headers: { "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: err.message }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});
