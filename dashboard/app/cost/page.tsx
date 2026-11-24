"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function CostPage() {
  const [rows, setRows] = useState<Array<Record<string, string>>>([]);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ data: Array<Record<string, string>> }>("/dashboard/cost/recent", tenantId)
      .then((body) => setRows(body.data))
      .catch(() => setRows([]));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Cost</h1>
        <ul className="space-y-2 text-sm">
          {rows.map((row) => (
            <li key={row.request_id} className="rounded border border-slate-800 p-3">
              <span className="font-medium text-slate-100">{row.model}</span> · cache {row.cache_status}{" "}
              · savings ${row.savings_usd}
            </li>
          ))}
        </ul>
      </div>
    </TenantGate>
  );
}
