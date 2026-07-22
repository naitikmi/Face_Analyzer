"use client";

import { useState } from "react";
import type { RecommendationItem } from "@/lib/types";

export default function RecommendationCard({ item }: { item: RecommendationItem }) {
  const [imageFailed, setImageFailed] = useState(false);
  const percent = Math.round(item.suitability_score * 100);

  return (
    <div className="grain-panel flex w-56 shrink-0 flex-col overflow-hidden rounded-2xl transition-transform duration-300 hover:-translate-y-1">
      <div className="relative aspect-square w-full overflow-hidden bg-void-deep">
        {!imageFailed ? (
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
        <div className="absolute right-2 top-2 rounded-full border border-brass/40 bg-void/80 px-2 py-0.5 text-[11px] font-medium text-brass-bright backdrop-blur-sm">
          {percent}% match
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-1.5 p-4">
        <h4 className="font-display text-base capitalize leading-tight text-ink">{item.style}</h4>
        <p className="text-xs leading-relaxed text-ink-dim">{item.description}</p>
      </div>
    </div>
  );
}
