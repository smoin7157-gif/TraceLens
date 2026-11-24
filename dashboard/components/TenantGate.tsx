"use client";

import type { ReactNode } from "react";

import { getStoredTenantId } from "@/lib/settings";

export function TenantGate({ children }: { children: ReactNode }) {
  const tenantId = getStoredTenantId();
  if (!tenantId) {
    return <p className="text-slate-400">Set a tenant ID in Settings to load this view.</p>;
  }
  return <>{children}</>;
}