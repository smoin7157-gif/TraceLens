"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function PromptsPage() {
  const [rows, setRows] = useState<Array<{ name: string; slug: string }>>([]);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ data: Array<{ name: string; slug: string }> }>("/dashboard/prompts", tenantId)
      .then((body) => setRows(body.data))
      .catch(() => setRows([]));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Prompts</h1>
        <ul className="space-y-2 text-sm">
          {rows.map((row) => (
            <li key={row.slug} className="rounded border border-slate-800 p-3">
              {row.name} <span className="text-slate-500">({row.slug})</span>
            </li>
          ))}
        </ul>
      </div>
    </TenantGate>
  );
}