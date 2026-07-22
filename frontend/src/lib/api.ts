import type { AnalyzeResponse, Gender, MaintenancePreference } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class AnalyzeError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
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
