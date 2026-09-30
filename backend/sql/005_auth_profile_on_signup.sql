-- Create a profiles row when a Supabase Auth user registers (apply on Supabase Postgres).

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (user_id)
    VALUES (NEW.id::text)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        EXECUTE 'DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users';
        EXECUTE $trigger$
            CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW
            EXECUTE FUNCTION public.handle_new_user()
        $trigger$;
    END IF;
END $$;
