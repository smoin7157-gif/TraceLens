const TENANT_KEY = "tracelens.tenant_id";

export function getStoredTenantId(): string {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(TENANT_KEY) ?? "";
}

export function setStoredTenantId(tenantId: string): void {
  window.localStorage.setItem(TENANT_KEY, tenantId);
}