"use client";

import { useState } from "react";

import { getApiBaseUrl } from "@/lib/api";
import { getStoredTenantId, setStoredTenantId } from "@/lib/settings";

export default function SettingsPage() {
  const [tenantId, setTenantId] = useState(getStoredTenantId());
  const [adminToken, setAdminToken] = useState("");
  const [seedResult, setSeedResult] = useState("");

  const saveTenant = () => setStoredTenantId(tenantId);

  const seedDemo = async () => {
    const response = await fetch(`${getApiBaseUrl()}/dashboard/demo/seed`, {
      method: "POST",
      headers: { "X-Admin-Token": adminToken },
    });
    if (!response.ok) {
      setSeedResult("Seed failed — check ADMIN token.");
      return;
    }
    const body = (await response.json()) as { tenant_id: string; api_key_secret: string };
    setStoredTenantId(body.tenant_id);
    setTenantId(body.tenant_id);
    setSeedResult(`Tenant ${body.tenant_id} seeded. API key: ${body.api_key_secret}`);
  };

  return (
    <div className="max-w-lg space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <label className="block text-sm">
        Tenant ID
        <input
          className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
        />
      </label>
      <button
        type="button"
        className="rounded bg-accent px-3 py-1 text-sm font-medium text-slate-900"
        onClick={saveTenant}
      >
        Save tenant
      </button>
      <label className="block text-sm">
        Admin token (seed demo tenant)
        <input
          className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1"
          type="password"
          value={adminToken}
          onChange={(e) => setAdminToken(e.target.value)}
        />
      </label>
      <button
        type="button"
        className="rounded border border-slate-600 px-3 py-1 text-sm"
        onClick={seedDemo}
      >
        Seed demo tenant
      </button>
      {seedResult ? <p className="text-sm text-slate-300">{seedResult}</p> : null}
      <p className="text-xs text-slate-500">API: {getApiBaseUrl()}</p>
    </div>
  );
}