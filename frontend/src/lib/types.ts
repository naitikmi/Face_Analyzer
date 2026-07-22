export type Gender = "male" | "female";
export type MaintenancePreference = "low" | "medium" | "high";

export interface FaceShapeInfo {
  shape: string;
  confidence: number;
  description: string;
  all_scores: Record<string, number>;
  measurements: Record<string, number>;
}

export interface RecommendationItem {
  style: string;
  style_slug: string;
  suitability_score: number;
  description: string;
  image_url: string;
}

export interface HairRecommendationItem extends RecommendationItem {
  gender: Gender;
}

export interface RecommendationSet {
  beard: RecommendationItem[];
  hair: HairRecommendationItem[];
  glasses: RecommendationItem[];
}

export interface ExtensionsInfo {
  skin_analysis: unknown | null;
  feedback_submission_url: string | null;
}

export interface AnalyzeResponse {
  face_detected: boolean;
  face_count: number;
  face_shape: FaceShapeInfo | null;
  recommendations: RecommendationSet | null;
  extensions: ExtensionsInfo;
}
