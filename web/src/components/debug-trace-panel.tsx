import type { RequestTrace } from "@/lib/types";

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export function DebugTracePanel({ trace }: { trace: RequestTrace }) {
  return (
    <details className="rounded-md border border-amber-200 bg-amber-50/80 p-3 text-xs text-slate-800">
      <summary className="cursor-pointer font-semibold text-amber-900">
        Debug trace (admin)
      </summary>
      <dl className="mt-3 grid gap-2 sm:grid-cols-2">
        <div>
          <dt className="font-medium text-slate-600">Query mode</dt>
          <dd>{trace.query_mode}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-600">Verification</dt>
          <dd>{trace.verification_outcome}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-600">Confidence</dt>
          <dd>{trace.confidence}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-600">Latency (ms)</dt>
          <dd>{trace.latency_ms.toFixed(1)}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="font-medium text-slate-600">Retrieval query</dt>
          <dd className="whitespace-pre-wrap font-mono">{trace.retrieval_query}</dd>
        </div>
      </dl>
      <div className="mt-3">
        <p className="font-medium text-slate-600">Retrieval snapshot</p>
        <pre className="mt-1 max-h-64 overflow-auto rounded bg-white p-2 font-mono text-[11px] leading-snug">
          {formatJson(trace.retrieval_snapshot)}
        </pre>
      </div>
    </details>
  );
}
