// Run with: npm test
import assert from "node:assert/strict";
import { test } from "node:test";
import { readContact, validateContact } from "./contact.ts";

const valid = {
  name: "Ada",
  company: "",
  email: "ada@plant.com",
  message: "Hello",
};

test("accepts a valid message without a company", () => {
  assert.deepEqual(validateContact(valid), {});
});

test("rejects missing fields and malformed email", () => {
  const errors = validateContact({ ...valid, name: "", email: "ada@plant" });
  assert.ok(errors.name);
  assert.ok(errors.email);
});

test("rejects oversized input", () => {
  assert.ok(validateContact({ ...valid, message: "x".repeat(4001) }).message);
});

test("trims form values and ignores non-string entries", () => {
  const form = new FormData();
  form.set("name", "  Ada  ");
  form.set("email", new Blob(["x"]));
  const values = readContact(form);
  assert.equal(values.name, "Ada");
  assert.equal(values.email, "");
});
