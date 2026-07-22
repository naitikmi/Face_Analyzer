"use client";

import type { AnalyzeResponse, RecommendationItem } from "@/lib/types";
import RecommendationCard from "./RecommendationCard";

function ShapeDistribution({ scores, leadingShape }: { scores: Record<string, number>; leadingShape: string }) {
  const entries = Object.entries(scores).sort((a, b) => b[1] - a[1]);
  return (
    <div className="flex flex-col gap-2.5">
      {entries.map(([shape, score]) => (
        <div key={shape} className="flex items-center gap-3">
          <span
            className={`w-20 shrink-0 text-xs capitalize tracking-wide ${
              shape === leadingShape ? "text-brass-bright" : "text-ink-dim"
            }`}
          >
            {shape}
          </span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-panel-line/60">
            <div
              className={`h-full rounded-full ${shape === leadingShape ? "bg-brass-bright" : "bg-panel-line"}`}
              style={{ width: `${Math.max(score * 100, 2)}%` }}
            />
          </div>
          <span className="w-9 shrink-0 text-right text-xs text-ink-dim">{Math.round(score * 100)}%</span>
        </div>
      ))}
    </div>
  );
}

function Rail({ title, items }: { title: string; items: RecommendationItem[] }) {
  if (items.length === 0) return null;
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <h3 className="font-display text-2xl italic text-ink">{title}</h3>
        <span className="rule flex-1 mx-4" />
        <span className="text-xs uppercase tracking-[0.2em] text-ink-dim">{items.length} picks</span>
      </div>
      <div className="rail flex gap-4 overflow-x-auto pb-3">
        {items.map((item) => (
          <RecommendationCard key={item.style_slug} item={item} />
        ))}
      </div>
    </section>
  );
}

export default function ResultsView({
  result,
  onReset,
}: {
  result: AnalyzeResponse;
  onReset: () => void;
}) {
  if (!result.face_detected || !result.face_shape || !result.recommendations) {
    return (
      <div className="reveal grain-panel mx-auto flex max-w-md flex-col items-center gap-4 rounded-3xl p-10 text-center">
        <p className="font-display text-2xl italic text-ink">We couldn&apos;t quite find your face</p>
        <p className="text-sm text-ink-dim">
          Try again with more even lighting, facing the camera directly, with your whole face in frame.
        </p>
        <button
          type="button"
          onClick={onReset}
          className="mt-2 rounded-full border border-brass/50 px-6 py-2.5 text-sm font-medium text-brass-bright transition-colors hover:bg-brass/10"
        >
          Try again
        </button>
      </div>
    );
  }

  const { face_shape, recommendations, face_count } = result;

  return (
    <div className="reveal flex flex-col gap-14">
      {face_count > 1 && (
        <div className="mx-auto w-full max-w-2xl rounded-xl border border-brass/30 bg-brass/10 px-4 py-2.5 text-center text-sm text-brass-bright">
          {face_count} faces detected — showing the reading for the most prominent one.
        </div>
      )}

      <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6 text-center">
        <span className="text-xs uppercase tracking-[0.3em] text-ink-dim">Your reading</span>
        <h2 className="font-display text-5xl italic capitalize text-ink sm:text-6xl">{face_shape.shape}</h2>
        <p className="max-w-md text-balance text-ink-dim">{face_shape.description}</p>
        <div className="w-full max-w-sm">
          <ShapeDistribution scores={face_shape.all_scores} leadingShape={face_shape.shape} />
        </div>
      </div>

      <div className="rule" />

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-12">
        <Rail title="Beard styles" items={recommendations.beard} />
        <Rail title="Hairstyles" items={recommendations.hair} />
        <Rail title="Glasses" items={recommendations.glasses} />
      </div>

      <div className="flex justify-center pb-4">
        <button
          type="button"
          onClick={onReset}
          className="rounded-full border border-brass/50 px-8 py-3 text-sm font-medium text-brass-bright transition-colors hover:bg-brass/10"
        >
          Start over
        </button>
      </div>
    </div>
  );
}
