"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { visualizeStyle, VisualizeError } from "@/lib/api";
import type { RecommendationItem, StyleCategory } from "@/lib/types";

type PreviewState = "idle" | "loading" | "ready" | "error" | "unavailable";

export default function RecommendationCard({
  item,
  category,
  originalImage,
}: {
  item: RecommendationItem;
  category: StyleCategory;
  originalImage: Blob | null;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const [previewState, setPreviewState] = useState<PreviewState>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  useEffect(() => {
    previewUrlRef.current = previewUrl;
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, []);

  const percent = Math.round(item.suitability_score * 100);

  const generatePreview = useCallback(async () => {
    if (!originalImage) return;
    setPreviewState("loading");
    setErrorMessage(null);
    try {
      const blob = await visualizeStyle(originalImage, category, item.style);
      const url = URL.createObjectURL(blob);
      setPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return url;
      });
      setPreviewState("ready");
    } catch (err) {
      if (err instanceof VisualizeError && err.notConfigured) {
        setPreviewState("unavailable");
      } else {
        setErrorMessage(err instanceof VisualizeError ? err.message : "Couldn't generate a preview.");
        setPreviewState("error");
      }
    }
  }, [originalImage, category, item.style]);

  const resetPreview = useCallback(() => {
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    setPreviewState("idle");
    setErrorMessage(null);
  }, []);

  const showingGenerated = previewState === "ready" && previewUrl;

  return (
    <div className="grain-panel flex w-56 shrink-0 flex-col overflow-hidden rounded-2xl transition-transform duration-300 hover:-translate-y-1">
      <div className="relative aspect-square w-full overflow-hidden bg-void-deep">
        {showingGenerated ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={previewUrl} alt={`You with ${item.style}`} className="h-full w-full object-cover" />
        ) : !imageFailed ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={item.image_url}
            alt={item.style}
            className="h-full w-full object-cover"
            onError={() => setImageFailed(true)}
            loading="lazy"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-ink-dim">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" className="opacity-50">
              <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.4" />
              <path d="M4 20c0-3.5 3.5-6 8-6s8 2.5 8 6" stroke="currentColor" strokeWidth="1.4" />
            </svg>
            <span className="px-3 text-center text-xs uppercase tracking-widest">Reference coming soon</span>
          </div>
        )}

        {previewState === "loading" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-void/80 backdrop-blur-sm">
            <div className="h-2.5 w-2.5 rounded-full bg-brass pulse-ring" />
            <span className="text-[11px] uppercase tracking-widest text-brass-bright">Generating…</span>
          </div>
        )}

        <div className="absolute right-2 top-2 rounded-full border border-brass/40 bg-void/80 px-2 py-0.5 text-[11px] font-medium text-brass-bright backdrop-blur-sm">
          {showingGenerated ? "Your preview" : `${percent}% match`}
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <h4 className="font-display text-base capitalize leading-tight text-ink">{item.style}</h4>
        <p className="text-xs leading-relaxed text-ink-dim">{item.description}</p>

        {originalImage && (
          <div className="mt-auto flex flex-col gap-1 pt-2">
            {showingGenerated ? (
              <button
                type="button"
                onClick={resetPreview}
                className="text-xs font-medium text-ink-dim underline decoration-brass/40 decoration-1 underline-offset-4 transition-colors hover:text-brass"
              >
                Back to reference
              </button>
            ) : previewState === "unavailable" ? (
              <span className="text-[11px] leading-snug text-ink-dim">Preview-on-me isn&apos;t set up yet.</span>
            ) : (
              <>
                <button
                  type="button"
                  onClick={generatePreview}
                  disabled={previewState === "loading"}
                  className="text-xs font-medium text-brass-bright underline decoration-brass/40 decoration-1 underline-offset-4 transition-colors hover:text-brass-bright/80 disabled:opacity-40"
                >
                  {previewState === "error" ? "Try again" : "Preview on me"}
                </button>
                {previewState === "idle" && (
                  <span className="text-[10px] leading-snug text-ink-dim/80">Sends your photo to Google&apos;s AI to generate this.</span>
                )}
                {previewState === "error" && errorMessage && (
                  <span className="text-[10px] leading-snug text-wine">{errorMessage}</span>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
