-- Messages sent through the site's contact form.
-- Limits mirror lib/contact.ts so a direct API call cannot bypass them.
create table public.contact_messages (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  name text not null check (char_length(name) between 1 and 120),
  company text check (char_length(company) <= 160),
  email text not null check (char_length(email) between 3 and 254),
  message text not null check (char_length(message) between 1 and 4000)
);

alter table public.contact_messages enable row level security;

-- Visitors may only add a message. No select, update or delete policy exists,
-- so the public API cannot read or change what was sent.
create policy "Anyone can send a message"
  on public.contact_messages
  for insert
  to anon
  with check (true);

revoke all on public.contact_messages from anon, authenticated;
grant insert (name, company, email, message) on public.contact_messages to anon;
