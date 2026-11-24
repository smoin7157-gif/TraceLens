"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { TenantGate } from "@/components/TenantGate";
import { TraceTree } from "@/components/TraceTree";
import { getApiBaseUrl } from "@/lib/api";
import { getStoredTenantId } from "@/lib/settings";

export default function TraceDetailPage() {
  const params = useParams<{ traceId: string }>();
  const tenantId = getStoredTenantId();
  const [tree, setTree] = useState<Array<{ id: string; name: string; kind: string; children?: [] }>>([]);

  useEffect(() => {
    if (!tenantId || !params.traceId) return;
    const url = new URL(`/dashboard/traces/${params.traceId}/tree`, getApiBaseUrl());
    url.searchParams.set("tenant_id", tenantId);
    fetch(url)
      .then((r) => r.json())
      .then((body) => setTree(body.tree ?? []))
      .catch(() => setTree([]));
  }, [tenantId, params.traceId]);

  return (
    <TenantGate>
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Trace {params.traceId}</h1>
        <TraceTree nodes={tree} />
      </div>
    </TenantGate>
  );
}