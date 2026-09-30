"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/auth-provider";

export default function HomePage() {
  const router = useRouter();
  const { accessToken, ready } = useAuth();

  useEffect(() => {
    if (!ready) {
      return;
    }
    router.replace(accessToken ? "/chat" : "/login");
  }, [ready, accessToken, router]);

  return null;
}
