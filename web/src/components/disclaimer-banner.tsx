const DEFAULT_DISCLAIMER =
  "LegalVault is a legal research assistant, not legal advice. Verify all citations against the underlying statute.";

export function DisclaimerBanner({ text }: { text?: string }) {
  return (
    <aside
      className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950"
      role="note"
      aria-label="Legal disclaimer"
    >
      {text ?? DEFAULT_DISCLAIMER}
    </aside>
  );
}
