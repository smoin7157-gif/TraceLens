"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Array<{ id: string; name: string }>>([]);
  const [experiments, setExperiments] = useState<Array<{ id: string; name: string; status: string }>>(
    [],
  );
  const [error, setError] = useState<string | null>(null);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    setError(null);
    Promise.all([
      fetchDashboard<{ data: Array<{ id: string; name: string }> }>("/dashboard/datasets", tenantId),
      fetchDashboard<{ experiments: Array<{ id: string; name: string; status: string }> }>(
        "/dashboard/datasets/experiments",
        tenantId,
      ),
    ])
      .then(([ds, ex]) => {
        setDatasets(ds.data);
        setExperiments(ex.experiments);
      })
      .catch((err: Error) => {
        setDatasets([]);
        setExperiments([]);
        setError(err.message);
      });
  }, [tenantId]);

  return (
    <TenantGate>
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Datasets & Experiments</h1>
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-slate-400">Datasets</h2>
          <ul className="space-y-2 text-sm">
            {datasets.map((row) => (
              <li key={row.id} className="rounded border border-slate-800 p-3">
                {row.name}
              </li>
            ))}
          </ul>
        </section>
        <section className="space-y-2">
          <h2 className="text-sm font-medium text-slate-400">Experiments</h2>
          <ul className="space-y-2 text-sm">
            {experiments.map((row) => (
              <li key={row.id} className="rounded border border-slate-800 p-3">
                {row.name} · {row.status}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </TenantGate>
  );
}