"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import CameraCapture from "./CameraCapture";
import ResultsView from "./ResultsView";
import { analyzeFace, AnalyzeError } from "@/lib/api";
import type { AnalyzeResponse, Gender, MaintenancePreference } from "@/lib/types";

type Step = "capture" | "analyzing" | "results";

const GENDERS: { value: Gender; label: string }[] = [
  { value: "male", label: "Men" },
  { value: "female", label: "Women" },
];

const MAINTENANCE_OPTIONS: { value: MaintenancePreference; label: string }[] = [
  { value: "low", label: "Low upkeep" },
  { value: "medium", label: "Some upkeep" },
  { value: "high", label: "Dedicated" },
];

const LOADING_LINES = [
  "Reading your proportions…",
  "Weighing jaw against brow…",
  "Cross-referencing the lookbook…",
];

export default function FaceAnalyzerApp() {
  const [step, setStep] = useState<Step>("capture");
  const [imageBlob, setImageBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [gender, setGender] = useState<Gender | null>(null);
  const [maintenance, setMaintenance] = useState<MaintenancePreference | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingLine, setLoadingLine] = useState(0);
  const previewUrlRef = useRef<string | null>(null);

  useEffect(() => {
    previewUrlRef.current = previewUrl;
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, []);

  useEffect(() => {
    if (step !== "analyzing") return;
    const id = setInterval(() => {
      setLoadingLine((n) => (n + 1) % LOADING_LINES.length);
    }, 1400);
    return () => clearInterval(id);
  }, [step]);

  const handleCapture = useCallback((blob: Blob, url: string) => {
    setImageBlob(blob);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return url;
    });
    setError(null);
  }, []);

  const handleRetake = useCallback(() => {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setImageBlob(null);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!imageBlob || !gender) return;
    setStep("analyzing");
    setError(null);
    try {
      const response = await analyzeFace(imageBlob, {
        gender,
        maintenancePreference: maintenance ?? undefined,
      });
      setResult(response);
      setStep("results");
    } catch (err) {
      const message =
        err instanceof AnalyzeError ? err.message : "Something went wrong while analyzing your photo.";
      setError(message);
      setStep("capture");
    }
  }, [imageBlob, gender, maintenance]);

  const handleReset = useCallback(() => {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setImageBlob(null);
    setResult(null);
    setError(null);
    setStep("capture");
  }, []);

  return (
    <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-5xl flex-col px-6 py-10 sm:px-10 sm:py-14">
      <header className="mb-12 flex items-center justify-between reveal">
        <div className="flex items-center gap-3">
          <MirrorMark />
          <span className="font-display text-lg tracking-wide text-ink">Atelier</span>
        </div>
        <span className="hidden text-xs uppercase tracking-[0.3em] text-ink-dim sm:block">
          Face &amp; Style Reading
        </span>
      </header>

      {step === "capture" && (
        <div className="flex flex-1 flex-col gap-14">
          <div className="reveal flex flex-col items-center gap-4 text-center" style={{ animationDelay: "60ms" }}>
            <h1 className="font-display text-4xl italic leading-[1.05] text-ink sm:text-6xl">
              Look closer.
              <br />
              <span className="text-brass-bright">Dress the face you have.</span>
            </h1>
            <p className="max-w-lg text-ink-dim">
              A quick photo tells us your face shape — then we curate beard, hair, and glasses styles built
              for it, not a generic average.
            </p>
          </div>

          <div className="reveal grid gap-10 sm:grid-cols-[1fr_auto_1fr] sm:items-start" style={{ animationDelay: "140ms" }}>
            <div className="flex flex-col items-center gap-4">
              {!previewUrl ? (
                <CameraCapture onCapture={handleCapture} />
              ) : (
                <div className="flex flex-col items-center gap-4">
                  <div className="relative aspect-square w-full max-w-sm overflow-hidden rounded-[2.5rem] border-2 border-brass/40 bg-panel shadow-[0_0_0_1px_rgba(201,161,90,0.08),0_30px_60px_-20px_rgba(0,0,0,0.75)]">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={previewUrl} alt="Your captured photo" className="h-full w-full object-cover" />
                    <div className="pointer-events-none absolute inset-4 rounded-[2rem] border border-brass/20" />
                  </div>
                  <button
                    type="button"
                    onClick={handleRetake}
                    className="text-sm font-medium text-ink-dim underline decoration-brass/40 decoration-1 underline-offset-4 transition-colors hover:text-brass"
                  >
                    Retake photo
                  </button>
                </div>
              )}
            </div>

            <div className="rule hidden sm:block sm:h-full sm:w-px" />

            <div className="flex flex-col gap-8">
              <div className="flex flex-col gap-3">
                <span className="text-xs uppercase tracking-[0.25em] text-ink-dim">Styling for</span>
                <div className="flex gap-3">
                  {GENDERS.map((g) => (
                    <button
                      key={g.value}
                      type="button"
                      onClick={() => setGender(g.value)}
                      className={`flex-1 rounded-full border px-5 py-3 text-sm font-medium transition-colors ${
                        gender === g.value
                          ? "border-brass bg-brass text-void-deep"
                          : "border-panel-line text-ink-dim hover:border-brass/50 hover:text-ink"
                      }`}
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-col gap-3">
                <span className="text-xs uppercase tracking-[0.25em] text-ink-dim">
                  Grooming upkeep <span className="opacity-60">(optional)</span>
                </span>
                <div className="flex flex-col gap-2">
                  {MAINTENANCE_OPTIONS.map((m) => (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setMaintenance((prev) => (prev === m.value ? null : m.value))}
                      className={`rounded-xl border px-4 py-2.5 text-left text-sm transition-colors ${
                        maintenance === m.value
                          ? "border-brass/60 bg-brass/10 text-brass-bright"
                          : "border-panel-line text-ink-dim hover:border-brass/40 hover:text-ink"
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <p className="rounded-xl border border-wine/50 bg-wine/10 px-4 py-3 text-sm text-ink">{error}</p>
              )}

              <button
                type="button"
                onClick={handleSubmit}
                disabled={!imageBlob || !gender}
                className="mt-2 rounded-full bg-brass px-8 py-3.5 text-sm font-semibold tracking-wide text-void-deep transition-all hover:bg-brass-bright disabled:cursor-not-allowed disabled:opacity-30"
              >
                Reveal my analysis
              </button>
              {!gender && imageBlob && (
                <p className="-mt-4 text-xs text-ink-dim">Choose who you&apos;re styling for to continue.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {step === "analyzing" && (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">
          <div className="relative flex h-20 w-20 items-center justify-center">
            <div className="absolute h-20 w-20 rounded-full border border-brass/30" />
            <div className="h-3 w-3 rounded-full bg-brass pulse-ring" />
          </div>
          <p className="font-display shimmer text-2xl italic">{LOADING_LINES[loadingLine]}</p>
        </div>
      )}

      {step === "results" && result && (
        <ResultsView result={result} previewUrl={previewUrl} originalImage={imageBlob} onReset={handleReset} />
      )}

      <footer className="mt-auto pt-16 text-center text-xs text-ink-dim/70">
        Your photo is analyzed in memory and never stored.
      </footer>
    </div>
  );
}

function MirrorMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="10" r="6.5" stroke="var(--brass)" strokeWidth="1.6" />
      <line x1="12" y1="16.5" x2="12" y2="21" stroke="var(--brass)" strokeWidth="1.6" />
      <circle cx="9.5" cy="7.5" r="0.9" fill="var(--brass-bright)" />
    </svg>
  );
}
