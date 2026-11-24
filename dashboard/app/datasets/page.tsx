"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function DatasetsPage() {
  const [experiments, setExperiments] = useState<Array<{ name: string; status: string }>>([]);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<{ experiments: Array<{ name: string; status: string }> }>(
      "/dashboard/datasets/experiments",
      tenantId,
    )
      .then((body) => setExperiments(body.experiments))
      .catch(() => setExperiments([]));
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Datasets & Experiments</h1>
        <ul className="space-y-2 text-sm">
          {experiments.map((row) => (
            <li key={row.name} className="rounded border border-slate-800 p-3">
              {row.name} · {row.status}
            </li>
          ))}
        </ul>
      </div>
    </TenantGate>
  );
}