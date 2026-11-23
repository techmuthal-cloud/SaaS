/**
 * Authenticated API Client for SellerFlow AI Web Client.
 * Automatically attaches Clerk session token (Authorization: Bearer <token>)
 * to all protected workspace and financial endpoints.
 */

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";

export async function fetchWithAuth<T = any>(
  path: string,
  options: RequestInit = {},
  getToken?: () => Promise<string | null>
): Promise<T> {
  const token = getToken ? await getToken() : null;
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE}${normalizedPath}`;

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = `Request failed (${res.status} ${res.statusText})`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // ignore json parse error
    }
    const err = new Error(errorDetail);
    (err as any).status = res.status;
    throw err;
  }

  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("text/csv") || contentType.includes("application/xml") || contentType.includes("application/octet-stream")) {
    return (await res.blob()) as unknown as T;
  }

  return (await res.json()) as T;
}

export { API_BASE };
