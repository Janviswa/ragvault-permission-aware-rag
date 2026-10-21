export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");

function messageFor(status: number, data: unknown): string {
  const detail =
    data && typeof data === "object" && "detail" in data ? (data as { detail?: unknown }).detail : undefined;
  const validationMessage =
    Array.isArray(detail) && detail[0] && typeof detail[0] === "object" && "msg" in detail[0]
      ? String((detail[0] as { msg: unknown }).msg)
      : undefined;
  if (typeof detail === "string") return detail;
  if (validationMessage) return validationMessage;
  if (status === 401) return "Authentication required";
  if (status === 403) return "You are not authorized to perform this action";
  return `Request failed (${status})`;
}

type RequestOptions = RequestInit & { authenticated?: boolean };

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured");
  }

  const { authenticated = true, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers);
  const isFormData =
    typeof FormData !== "undefined" && requestOptions.body instanceof FormData;

  if (authenticated) {
    const token = localStorage.getItem("access_token");
    if (!token) {
      throw new ApiError("Authentication required", 401);
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (requestOptions.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...requestOptions,
      headers,
    });
  } catch {
    throw new Error("Can't reach the server. Check that the backend is running.");
  }

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    if (response.status === 401 && authenticated) {
      localStorage.removeItem("access_token");
    }

    const message = messageFor(response.status, data);
    throw new ApiError(message, response.status);
  }

  if (data === undefined) {
    throw new Error("The server returned an invalid response");
  }

  return data as T;
}

/**
 * POST and read a Server-Sent Events response as it arrives.
 * `onEvent` is called once per event ({event, data}). Abort the `signal` to stop (the server then
 * stops generating and saves what was written so far).
 */
export async function streamRequest(
  path: string,
  options: { body: unknown; signal?: AbortSignal; onEvent: (event: string, data: any) => void }, // eslint-disable-line @typescript-eslint/no-explicit-any
): Promise<void> {
  if (!API_URL) throw new Error("NEXT_PUBLIC_API_URL is not configured");
  const token = localStorage.getItem("access_token");
  if (!token) throw new ApiError("Authentication required", 401);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") throw cause;
    throw new Error("Can't reach the server. Check that the backend is running.");
  }

  if (!response.ok) {
    if (response.status === 401) localStorage.removeItem("access_token");
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = undefined;
    }
    throw new ApiError(messageFor(response.status, data), response.status);
  }
  if (!response.body) throw new Error("Streaming isn't supported by this browser");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end: number;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) options.onEvent(event, JSON.parse(data));
    }
  }
}
