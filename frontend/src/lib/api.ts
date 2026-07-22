import type { AnalyzeResponse, Gender, MaintenancePreference, StyleCategory } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class AnalyzeError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export class VisualizeError extends Error {
  status: number;
  /** true when the backend has no GEMINI_API_KEY configured (503) - not a per-request failure. */
  notConfigured: boolean;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.notConfigured = status === 503;
  }
}

export async function analyzeFace(
  image: Blob,
  options: { gender?: Gender; maintenancePreference?: MaintenancePreference } = {}
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("image", image, "capture.jpg");
  if (options.gender) form.append("gender", options.gender);
  if (options.maintenancePreference) {
    form.append("maintenance_preference", options.maintenancePreference);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new AnalyzeError(
      "Could not reach the analysis service. Check your connection and try again.",
      0
    );
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new AnalyzeError(
      typeof body.detail === "string" ? body.detail : `Request failed with status ${res.status}`,
      res.status
    );
  }

  return res.json();
}

/**
 * Generate a "preview on me" image: the user's own photo edited to show
 * the given style. Sends the photo to the backend, which sends it on to
 * Gemini for the edit - nothing is persisted on either side.
 */
export async function visualizeStyle(
  image: Blob,
  category: StyleCategory,
  style: string
): Promise<Blob> {
  const form = new FormData();
  form.append("image", image, "capture.jpg");
  form.append("category", category);
  form.append("style", style);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/visualize`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new VisualizeError("Could not reach the preview service. Check your connection and try again.", 0);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new VisualizeError(
      typeof body.detail === "string" ? body.detail : `Request failed with status ${res.status}`,
      res.status
    );
  }

  return res.blob();
}
