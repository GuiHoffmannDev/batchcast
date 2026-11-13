"use server";

import {
  readContact,
  validateContact,
  type ContactErrors,
  type ContactValues,
} from "@/lib/contact";

export type ContactState = {
  status: "idle" | "sent" | "error";
  message?: string;
  errors?: ContactErrors;
  values?: ContactValues;
};

// shortcut: no rate limiting; the table is insert-only and size-capped. Add a limiter if spam appears.
export async function sendMessage(
  _previous: ContactState,
  form: FormData,
): Promise<ContactState> {
  // Honeypot: people never see this field, so a value means a bot. Report success and store nothing.
  if (form.get("website")) return { status: "sent" };

  const values = readContact(form);
  const errors = validateContact(values);
  if (Object.keys(errors).length > 0) {
    return { status: "error", errors, values, message: "Check the fields below." };
  }

  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    console.error("Contact form: SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY is not set.");
    return {
      status: "error",
      values,
      message: "The message was not sent. The contact form is not set up yet.",
    };
  }

  try {
    const response = await fetch(`${url}/rest/v1/contact_messages`, {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        Prefer: "return=minimal",
      },
      body: JSON.stringify({ ...values, company: values.company || null }),
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) throw new Error(`Supabase responded ${response.status}`);
  } catch (error) {
    console.error("Contact form: insert failed.", error);
    return {
      status: "error",
      values,
      message: "The message was not sent. Try again in a moment.",
    };
  }

  return { status: "sent" };
}
