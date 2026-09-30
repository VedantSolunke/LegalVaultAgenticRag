import { formatQueryMode } from "@/lib/api/client";
import type { ResearchResponse } from "@/lib/types";

import { AdminDebugTrace } from "./admin-debug-trace";
import { CitationCard } from "./citation-card";
import { DisclaimerBanner } from "./disclaimer-banner";

function confidenceLabel(confidence: string): string {
  return confidence.replaceAll("_", " ");
}

export function ResearchMessage({
  research,
  accessToken,
  isAdmin,
}: {
  research: ResearchResponse;
  accessToken?: string | null;
  isAdmin?: boolean;
}) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
        <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium uppercase tracking-wide">
          {formatQueryMode(research.query_mode)}
        </span>
        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-800">
          Confidence: {confidenceLabel(research.confidence)}
        </span>
      </div>
      <p className="text-base font-medium text-slate-900">{research.lead}</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">
        {research.body}
      </p>
      {research.citations.length > 0 && (
        <section className="space-y-2" aria-label="Citations">
          <h3 className="text-sm font-semibold text-slate-800">Citations</h3>
          <div className="space-y-2">
            {research.citations.map((citation) => (
              <CitationCard key={`${citation.act}-${citation.section_number}`} citation={citation} />
            ))}
          </div>
        </section>
      )}
      <DisclaimerBanner text={research.disclaimer} />
      {isAdmin && accessToken && research.trace_id && (
        <AdminDebugTrace accessToken={accessToken} traceId={research.trace_id} />
      )}
    </div>
  );
}
