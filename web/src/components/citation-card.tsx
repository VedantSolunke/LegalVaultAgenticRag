"use client";

import type { SectionCitation } from "@/lib/types";

export function CitationCard({ citation }: { citation: SectionCitation }) {
  return (
    <details className="group rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <summary className="cursor-pointer list-none font-medium text-slate-900 marker:content-none">
        <span className="text-slate-600">{citation.act}</span>{" "}
        Section {citation.section_number}
        <span className="font-normal text-slate-600"> — {citation.title}</span>
        {citation.ipc_section_number != null && (
          <span className="ml-2 text-xs text-slate-500">
            (IPC {citation.ipc_section_number})
          </span>
        )}
        <span className="ml-2 text-xs text-slate-400 group-open:hidden">
          Show excerpt
        </span>
      </summary>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
        {citation.excerpt}
      </p>
      {citation.mapping_source && (
        <p className="mt-2 text-xs text-slate-500">
          Mapping source: {citation.mapping_source}
        </p>
      )}
    </details>
  );
}
