"use client";

import { useActionState } from "react";
import { sendMessage, type ContactState } from "@/app/actions";
import type { ContactValues } from "@/lib/contact";

const initial: ContactState = { status: "idle" };

const fields: { name: keyof ContactValues; label: string; type: string; autoComplete: string; required: boolean }[] = [
  { name: "name", label: "Name", type: "text", autoComplete: "name", required: true },
  { name: "company", label: "Company (optional)", type: "text", autoComplete: "organization", required: false },
  { name: "email", label: "Email", type: "email", autoComplete: "email", required: true },
];

const inputClass =
  "mt-2 w-full rounded-lg border border-steel bg-white px-4 py-3 text-ink aria-invalid:border-alert";

export function ContactForm() {
  const [state, action, pending] = useActionState(sendMessage, initial);

  if (state.status === "sent") {
    return (
      <p role="status" className="rounded-lg border border-line bg-white p-6 text-lg">
        Message sent. We will reply by email.
      </p>
    );
  }

  return (
    <form action={action} className="grid gap-6" noValidate>
      {state.message && (
        <p role="alert" className="font-medium text-alert">
          {state.message}
        </p>
      )}

      {fields.map((field) => {
        const error = state.errors?.[field.name];
        return (
          <div key={field.name}>
            <label htmlFor={field.name} className="font-medium">
              {field.label}
            </label>
            <input
              id={field.name}
              name={field.name}
              type={field.type}
              autoComplete={field.autoComplete}
              required={field.required}
              defaultValue={state.values?.[field.name]}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? `${field.name}-error` : undefined}
              className={inputClass}
            />
            {error && (
              <p id={`${field.name}-error`} className="mt-2 text-sm text-alert">
                {error}
              </p>
            )}
          </div>
        );
      })}

      <div>
        <label htmlFor="message" className="font-medium">
          Message
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          required
          defaultValue={state.values?.message}
          aria-invalid={state.errors?.message ? true : undefined}
          aria-describedby={state.errors?.message ? "message-error" : undefined}
          className={inputClass}
        />
        {state.errors?.message && (
          <p id="message-error" className="mt-2 text-sm text-alert">
            {state.errors.message}
          </p>
        )}
      </div>

      {/* Honeypot: hidden from people and assistive technology; bots fill it in. */}
      <div className="hidden" aria-hidden="true">
        <label htmlFor="website">Website</label>
        <input id="website" name="website" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <button
        type="submit"
        disabled={pending}
        className="justify-self-start rounded-full bg-ink px-7 py-3 font-medium text-foam hover:bg-ink/80 disabled:opacity-60"
      >
        {pending ? "Sending message" : "Send message"}
      </button>
    </form>
  );
}
