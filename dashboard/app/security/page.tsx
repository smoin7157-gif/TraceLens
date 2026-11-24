"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function SecurityPage() {
  const [summary, setSummary] = useState<{ blocked_or_error_requests: number; total_reviewed: number } | null>(null);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ blocked_or_error_requests: number; total_reviewed: number }>(
      "/dashboard/security/summary",
      tenantId,
    )
      .then(setSummary)
      .catch(() => setSummary(null));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Security</h1>
        <p className="text-slate-300">
          Blocked / non-completed requests: {summary?.blocked_or_error_requests ?? "—"} /{" "}
          {summary?.total_reviewed ?? "—"}
        </p>
      </div>
    </TenantGate>
  );
}