# Admin flag for debug traces

Status: accepted

Operator visibility uses a boolean on the user profile (e.g. `is_admin`) enforced with Supabase RLS. The default UI shows research responses with citations and confidence; the debug trace panel is shown only when `is_admin` is true.
