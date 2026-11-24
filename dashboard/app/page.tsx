"use client";

import { useEffect, useState } from "react";

import { LiveChart } from "@/components/LiveChart";
import { fetchDashboard } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

type Overview = {
  live: { requests_per_second: number; success_rate: number };
  economics: { request_count: number; total_savings_usd: string; cache_hit_rate: number };
};

export default function OverviewPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const tenantId = getStoredTenantId();

  useEffect(() => {
    if (!tenantId) return;
    fetchDashboard<Overview>("/dashboard/overview", tenantId)
      .then(setOverview)
      .catch(() => setOverview(null));
  }, [tenantId]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Overview</h1>
      {!tenantId ? (
        <p className="text-slate-400">Set a tenant ID in Settings to load tenant metrics.</p>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <Stat label="Requests (sample)" value={String(overview?.economics.request_count ?? "—")} />
            <Stat
              label="Cache hit rate"
              value={overview ? `${(overview.economics.cache_hit_rate * 100).toFixed(1)}%` : "—"}
            />
            <Stat label="Savings (USD)" value={overview?.economics.total_savings_usd ?? "—"} />
          </section>
          <section className="rounded-lg border border-slate-800 bg-panel p-4">
            <h2 className="mb-3 text-sm font-medium text-slate-300">Live gateway throughput</h2>
            <LiveChart />
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-panel p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}
