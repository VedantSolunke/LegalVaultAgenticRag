import type { ReactNode } from "react";

export const authFieldClassName =
  "mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm";

export const authLabelClassName = "block text-sm font-medium text-slate-700";

type AuthCardProps = {
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
};

export function AuthCard({ title, description, children, footer }: AuthCardProps) {
  return (
    <div className="mx-auto w-full max-w-md space-y-6 rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>
      {children}
      {footer}
    </div>
  );
}
