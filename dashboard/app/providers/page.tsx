"use client";

import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { getApiBaseUrl } from "@/lib/api";

type ProviderRow = {
  provider: string;
  model: string;
  circuit_state: string;
  p95_latency_ms: number;
  error_rate: number;
};

export default function ProvidersPage() {
  const [rows, setRows] = useState<ProviderRow[]>([]);

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/health/providers`)
      .then((r) => r.json())
      .then((body) => setRows(body.data ?? []))
      .catch(() => setRows([]));
  }, []);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Providers</h1>
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-900 text-left text-slate-400">
              <tr>
                <th className="px-3 py-2">Model</th>
                <th className="px-3 py-2">Circuit</th>
                <th className="px-3 py-2">P95 ms</th>
                <th className="px-3 py-2">Error rate</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.model} className="border-t border-slate-800">
                  <td className="px-3 py-2">{row.model}</td>
                  <td className="px-3 py-2">{row.circuit_state}</td>
                  <td className="px-3 py-2">{row.p95_latency_ms.toFixed(1)}</td>
                  <td className="px-3 py-2">{row.error_rate.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </TenantGate>
  );
}