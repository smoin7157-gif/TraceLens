"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function TracesPage() {
  const [rows, setRows] = useState<Array<{ trace_id: string; created_at: string }>>([]);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ data: Array<{ trace_id: string; created_at: string }> }>(
      "/dashboard/traces",
      tenantId,
    )
      .then((body) => setRows(body.data))
      .catch(() => setRows([]));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Trace Explorer</h1>
        <ul className="space-y-2 text-sm">
          {rows.map((row) => (
            <li key={row.trace_id}>
              <Link className="text-accent hover:underline" href={`/traces/${row.trace_id}`}>
                {row.trace_id}
              </Link>
              <span className="ml-2 text-slate-500">{row.created_at}</span>
            </li>
          ))}
        </ul>
      </div>
    </TenantGate>
  );
}