// API Types
export interface GenerateRequestModel {
  tema: string;
  longitud_texto: number;
  tono_texto: string;
  min_score_fuente: number;
  num_fuentes_scraper: number;
  num_resultados_scraper: number;
  min_score_generador: number;
  num_fuentes_generador: number;
  num_imagenes_buscar: number;
}

export interface ConfigBase {
  longitud_texto: number;
  tono_texto: string;
  min_score_fuente: number;
  num_fuentes_scraper: number;
  num_resultados_scraper: number;
  min_score_generador: number;
  num_fuentes_generador: number;
  num_imagenes_buscar: number;
}

export interface GeneratedArticleSummary {
  id: number;
  title: string;
  tema: string;
  created_at: string;
  status: string;
}

export interface GeneratedArticleDB {
  id: number;
  title: string;
  tema: string;
  body: string;
  created_at: string;
  status: string;
  meta_description?: string;
  image_url?: string; // Añadido para la URL de la imagen principal
  image_caption?: string; // Añadido para el pie de foto de la imagen principal
  sources_score?: number;
}

export interface GeneratedArticleUpdate {
  body: string;
  title?: string;
  meta_description?: string;
}

export interface APIResponse {
  message: string;
  article_id?: number;
  filename?: string;
}

export interface SuggestionsResponse {
  suggestions: string;
}

export interface RewriteResponse {
  rewritten_text: string;
}
