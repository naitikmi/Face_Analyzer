# Style reference images

This directory holds the reference photo shown on each recommendation card.
Drop images in directly - no code changes needed, since the backend builds
`image_url` from the style name alone.

## Convention

```
public/styles/beard/{slug}.jpg
public/styles/hair/male/{slug}.jpg
public/styles/hair/female/{slug}.jpg
public/styles/glasses/{slug}.jpg
```

`{slug}` is the style name from `backend/config.yaml`, lowercased with
spaces replaced by hyphens (see `slugify()` in
`backend/face_analyzer/api/pipeline.py`). For example the beard style
`"van dyke"` maps to `public/styles/beard/van-dyke.jpg`.

## Current status

No real photos are included yet - this is content work (sourcing or
licensing photography), not code work. Until images are added, the frontend
(`RecommendationCard.tsx`) shows a graceful placeholder card instead of a
broken image, so the app is fully usable without them.

Recommended size: square, at least 480x480px, consistent lighting/framing
across the set so the results grid feels cohesive.
