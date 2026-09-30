"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/auth-provider";

export function AuthRedirectIfSignedIn() {
  const router = useRouter();
  const { accessToken, ready } = useAuth();

  useEffect(() => {
    if (ready && accessToken) {
      router.replace("/chat");
    }
  }, [accessToken, ready, router]);

  return null;
}
