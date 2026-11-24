"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function AlertsPage() {
  const [rows, setRows] = useState<Array<{ name: string; metric: string; threshold: number }>>([]);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ data: Array<{ name: string; metric: string; threshold: number }> }>(
      "/dashboard/alerts",
      tenantId,
    )
      .then((body) => setRows(body.data))
      .catch(() => setRows([]));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <ul className="space-y-2 text-sm">
          {rows.map((row) => (
            <li key={row.name} className="rounded border border-slate-800 p-3">
              {row.name} · {row.metric} ≥ {row.threshold}
            </li>
          ))}
        </ul>
      </div>
    </TenantGate>
  );
}