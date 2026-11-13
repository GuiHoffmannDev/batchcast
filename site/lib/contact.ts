export type ContactValues = {
  name: string;
  company: string;
  email: string;
  message: string;
};

export type ContactErrors = Partial<Record<keyof ContactValues, string>>;

// Mirrored by the check constraints in supabase/migrations/0001_contact_messages.sql.
const LIMITS = { name: 120, company: 160, email: 254, message: 4000 } as const;
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function readContact(form: FormData): ContactValues {
  const text = (key: string) => {
    const value = form.get(key);
    return typeof value === "string" ? value.trim() : "";
  };
  return {
    name: text("name"),
    company: text("company"),
    email: text("email"),
    message: text("message"),
  };
}

export function validateContact(values: ContactValues): ContactErrors {
  const errors: ContactErrors = {};
  if (!values.name) errors.name = "Enter your name.";
  if (!values.email) errors.email = "Enter your email address.";
  else if (!EMAIL.test(values.email))
    errors.email = "Enter an email address like name@company.com.";
  if (!values.message) errors.message = "Write a message.";

  for (const key of Object.keys(LIMITS) as (keyof ContactValues)[]) {
    if (values[key].length > LIMITS[key])
      errors[key] = `Use ${LIMITS[key]} characters or fewer.`;
  }
  return errors;
}
