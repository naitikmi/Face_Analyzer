"use client";

import type { AnalyzeResponse, FeatureInsight, RecommendationItem } from "@/lib/types";
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

function FeatureCard({ note }: { note: FeatureInsight }) {
  const isFlattering = note.verdict === "flattering";
  return (
    <div className="grain-panel flex flex-col gap-3 rounded-2xl p-5">
      <div className="flex items-center justify-between gap-3">
        <h4 className="font-display text-lg text-ink">{note.feature}</h4>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ${
            isFlattering
              ? "border-brass/50 bg-brass/10 text-brass-bright"
              : "border-sage/50 bg-sage/10 text-sage"
          }`}
        >
          {isFlattering ? "Flattering" : "Styling opportunity"}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-ink-dim">{note.observation}</p>
      <div className="rule" />
      <p className="text-sm leading-relaxed text-ink">
        <span className="font-medium text-brass-bright">Try this — </span>
        {note.tip}
      </p>
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
  previewUrl,
  onReset,
}: {
  result: AnalyzeResponse;
  previewUrl: string | null;
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

  const { face_shape, recommendations, face_count, feature_insights } = result;

  return (
    <div className="reveal flex flex-col gap-14">
      {face_count > 1 && (
        <div className="mx-auto w-full max-w-2xl rounded-xl border border-brass/30 bg-brass/10 px-4 py-2.5 text-center text-sm text-brass-bright">
          {face_count} faces detected — showing the reading for the most prominent one.
        </div>
      )}

      <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-6 text-center">
        <span className="text-xs uppercase tracking-[0.3em] text-ink-dim">Your reading</span>

        {previewUrl && (
          <div className="relative h-32 w-32 overflow-hidden rounded-full border-2 border-brass/50 shadow-[0_0_0_1px_rgba(201,161,90,0.1),0_20px_40px_-15px_rgba(0,0,0,0.7)] sm:h-40 sm:w-40">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={previewUrl} alt="The photo you submitted" className="h-full w-full object-cover" />
          </div>
        )}

        <h2 className="font-display text-5xl italic capitalize text-ink sm:text-6xl">{face_shape.shape}</h2>
        <p className="max-w-md text-balance text-ink-dim">{face_shape.description}</p>
        <div className="w-full max-w-sm">
          <ShapeDistribution scores={face_shape.all_scores} leadingShape={face_shape.shape} />
        </div>
      </div>

      <div className="rule" />

      {feature_insights && feature_insights.length > 0 && (
        <>
          <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
            <div className="flex flex-col items-center gap-2 text-center">
              <h3 className="font-display text-3xl italic text-ink">Feature by feature</h3>
              <p className="max-w-lg text-sm text-ink-dim">
                What&apos;s already working, and where a style choice can enhance or balance a feature further.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {feature_insights.map((note) => (
                <FeatureCard key={note.feature} note={note} />
              ))}
            </div>
          </div>
          <div className="rule" />
        </>
      )}

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
