import {
  APIResponse,
  ConfigBase,
  GeneratedArticleDB,
  GeneratedArticleSummary,
  GeneratedArticleUpdate,
  GenerateRequestModel,
  RewriteResponse,
  SuggestionsResponse
} from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

class APIService {
  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async generateArticle(data: GenerateRequestModel): Promise<APIResponse> {
    return this.fetchWithErrorHandling<APIResponse>('/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getConfig(tema: string = 'Defecto'): Promise<ConfigBase> {
    return this.fetchWithErrorHandling<ConfigBase>(`/config/${tema}`);
  }

  async updateConfig(data: any): Promise<APIResponse> {
    return this.fetchWithErrorHandling<APIResponse>('/config', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getArticles(): Promise<GeneratedArticleSummary[]> {
    return this.fetchWithErrorHandling<GeneratedArticleSummary[]>('/articles');
  }

  async getArticle(articleId: number): Promise<GeneratedArticleDB> {
    return this.fetchWithErrorHandling<GeneratedArticleDB>(`/articles/${articleId}`);
  }

  async updateArticle(articleId: number, data: GeneratedArticleUpdate): Promise<APIResponse> {
    return this.fetchWithErrorHandling<APIResponse>(`/articles/${articleId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async generateSuggestions(articleId: number): Promise<SuggestionsResponse> {
    return this.fetchWithErrorHandling<SuggestionsResponse>(`/articles/${articleId}/generate-suggestions`, {
      method: 'POST',
    });
  }

  async rewriteArticle(articleId: number, textToRewrite: string, instruction: string): Promise<RewriteResponse> {
    return this.fetchWithErrorHandling<RewriteResponse>(`/articles/${articleId}/rewrite`, {
      method: 'POST',
      body: JSON.stringify({
        text_to_rewrite: textToRewrite,
        instruction: instruction,
      }),
    });
  }

  async publishArticle(articleId: number): Promise<APIResponse> {
    return this.fetchWithErrorHandling<APIResponse>(`/articles/${articleId}/publish`, {
      method: 'POST',
    });
  }
}

export const apiService = new APIService();
