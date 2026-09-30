"use client";

import { useEffect, useState } from "react";

import { fetchRequestTrace } from "@/lib/api/client";
import type { RequestTrace } from "@/lib/types";

import { DebugTracePanel } from "./debug-trace-panel";

export function AdminDebugTrace({
  accessToken,
  traceId,
}: {
  accessToken: string;
  traceId: string;
}) {
  const [trace, setTrace] = useState<RequestTrace | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setTrace(null);
    setError(null);
    fetchRequestTrace(accessToken, traceId)
      .then((payload) => {
        if (!cancelled) {
          setTrace(payload);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load trace");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, traceId]);

  if (error) {
    return (
      <p className="text-xs text-amber-800" role="status">
        Debug trace unavailable: {error}
      </p>
    );
  }
  if (!trace) {
    return <p className="text-xs text-slate-500">Loading debug trace…</p>;
  }
  return <DebugTracePanel trace={trace} />;
}
