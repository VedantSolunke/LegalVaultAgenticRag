# Invite-only Supabase authentication

Status: accepted (registration policy superseded for public deploy by ADR-0014)

v1 uses Supabase Auth with accounts created or enabled by the operator only—no public self-registration. This matches a small trusted user group on a free-tier stack without building org/tenant features. Wider access later may use an email allowlist before opening registration.
