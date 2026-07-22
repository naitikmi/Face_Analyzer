"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  onCapture: (blob: Blob, previewUrl: string) => void;
}

type CameraState = "starting" | "live" | "unavailable";

export default function CameraCapture({ onCapture }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<CameraState>("starting");

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setState("unavailable");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 960 }, height: { ideal: 960 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setState("live");
      } catch {
        if (!cancelled) setState("unavailable");
      }
    }

    startCamera();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const capture = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.videoWidth === 0) return;

    const size = Math.min(video.videoWidth, video.videoHeight);
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const sx = (video.videoWidth - size) / 2;
    const sy = (video.videoHeight - size) / 2;
    // Mirror horizontally so the capture matches what the user saw in preview
    ctx.translate(size, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, sx, sy, size, size, 0, 0, size, size);

    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob, URL.createObjectURL(blob));
      },
      "image/jpeg",
      0.9
    );
  }, [onCapture]);

  const handleFile = useCallback(
    (file: File | undefined) => {
      if (!file) return;
      onCapture(file, URL.createObjectURL(file));
    },
    [onCapture]
  );

  return (
    <div className="flex flex-col items-center gap-7">
      <div className="relative aspect-square w-full max-w-sm overflow-hidden rounded-[2.5rem] border-2 border-brass/40 bg-panel shadow-[0_0_0_1px_rgba(201,161,90,0.08),0_30px_60px_-20px_rgba(0,0,0,0.75)]">
        {state !== "unavailable" ? (
          <video ref={videoRef} className="h-full w-full scale-x-[-1] object-cover" playsInline muted />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3 px-8 text-center text-ink-dim">
            <p className="font-display text-lg italic text-ink">No camera access</p>
            <p className="text-sm">Upload a photo instead — the link below works either way.</p>
          </div>
        )}
        {state === "starting" && (
          <div className="absolute inset-0 flex items-center justify-center bg-void/60">
            <div className="h-3 w-3 rounded-full bg-brass pulse-ring" />
          </div>
        )}
        <div className="pointer-events-none absolute inset-4 rounded-[2rem] border border-brass/20" />
      </div>

      <canvas ref={canvasRef} className="hidden" />

      <div className="flex flex-col items-center gap-4 sm:flex-row">
        <button
          type="button"
          onClick={capture}
          disabled={state !== "live"}
          className="group relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-2 border-brass bg-transparent transition-transform hover:scale-105 disabled:opacity-30 disabled:hover:scale-100"
          aria-label="Capture photo"
        >
          <span className="h-11 w-11 rounded-full bg-brass transition-colors group-hover:bg-brass-bright" />
        </button>

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="text-sm font-medium text-ink-dim underline decoration-brass/40 decoration-1 underline-offset-4 transition-colors hover:text-brass"
        >
          Upload a photo instead
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="user"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
    </div>
  );
}
