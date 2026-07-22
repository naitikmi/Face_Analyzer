"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { visualizeStyle, VisualizeError } from "@/lib/api";
import type { RecommendationItem, StyleCategory } from "@/lib/types";

type PreviewState = "idle" | "loading" | "ready" | "error" | "unavailable";

/**
 * Placeholder art shown until a real reference photo (or a generated
 * preview) exists for a given style - distinct per category rather than
 * one generic icon for everything, so the empty state still says
 * something ("this is a beard card" / "this is glasses") at a glance.
 */
function CategoryIcon({ category }: { category: StyleCategory }) {
  if (category === "beard") {
    return (
      <svg width="34" height="34" viewBox="0 0 24 24" fill="none" className="opacity-50">
        <path
          d="M6 5c0 6 .5 9 2.5 11.5C10 18.5 11 19 12 19s2-.5 3.5-2.5C17.5 14 18 11 18 5"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path d="M9 15.5v2M12 16.5v2.5M15 15.5v2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
      </svg>
    );
  }
  if (category === "glasses") {
    return (
      <svg width="34" height="34" viewBox="0 0 24 24" fill="none" className="opacity-50">
        <circle cx="7" cy="12" r="4" stroke="currentColor" strokeWidth="1.4" />
        <circle cx="17" cy="12" r="4" stroke="currentColor" strokeWidth="1.4" />
        <path d="M11 12h2" stroke="currentColor" strokeWidth="1.4" />
        <path d="M3 12l-1.5-1M21 12l1.5-1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" className="opacity-50">
      <rect x="5" y="5" width="14" height="4" rx="1" stroke="currentColor" strokeWidth="1.4" />
      <path d="M7 9v10M10 9v10M13 9v10M16 9v10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

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
            <CategoryIcon category={category} />
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
