import { AuthPage } from "@/components/auth-page";
import { AuthCallbackHandler } from "@/components/auth-callback-handler";

export default function AuthCallbackPage() {
  return (
    <AuthPage>
      <AuthCallbackHandler />
    </AuthPage>
  );
}
