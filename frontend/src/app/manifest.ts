import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Atelier — Face & Style Analysis",
    short_name: "Atelier",
    description:
      "Camera-based face shape analysis with curated beard, hair, and glasses recommendations.",
    start_url: "/",
    display: "standalone",
    background_color: "#14110f",
    theme_color: "#14110f",
    orientation: "portrait-primary",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icon-512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
