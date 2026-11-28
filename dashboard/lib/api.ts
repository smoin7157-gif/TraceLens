export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_TRACELENS_API_URL ?? "http://localhost:8000";
}

export function getDashboardHeaders(): HeadersInit {
  const token = process.env.NEXT_PUBLIC_DASHBOARD_TOKEN;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export class DashboardApiError extends Error {
  constructor(
    readonly status: number,
    readonly path: string,
    message?: string,
  ) {
    super(message ?? `Dashboard API ${status}: ${path}`);
    this.name = "DashboardApiError";
  }
}

export async function fetchDashboard<T>(
  path: string,
  tenantId: string,
  init?: RequestInit,
): Promise<T> {
  const url = new URL(path, getApiBaseUrl());
  url.searchParams.set("tenant_id", tenantId);
  const response = await fetch(url.toString(), {
    ...init,
    headers: {
      ...getDashboardHeaders(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new DashboardApiError(response.status, path);
  }
  return response.json() as Promise<T>;
}