export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_TRACELENS_API_URL ?? "http://localhost:8000";
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
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Dashboard API ${response.status}: ${path}`);
  }
  return response.json() as Promise<T>;
}