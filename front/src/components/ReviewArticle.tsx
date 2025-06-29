import {
  ArrowLeft,
  Calendar,
  CheckSquare,
  Edit3,
  Save,
  Send,
  Sparkles,
  Square,
  Target,
  Wand2
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { GeneratedArticleDB } from '../types/api';
import Alert from './Alert';
import LoadingSpinner from './LoadingSpinner';

interface ReviewArticleProps {
  articleId: number | null;
  onBack: () => void;
}

const ReviewArticle: React.FC<ReviewArticleProps> = ({ articleId, onBack }) => {
  const [article, setArticle] = useState<GeneratedArticleDB | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [generatingSuggestions, setGeneratingSuggestions] = useState(false);
  const [applyingSuggestions, setApplyingSuggestions] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState<Set<number>>(new Set());
  const [alert, setAlert] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    console.log("articleId en useEffect:", articleId);
    if (articleId) {
      loadArticle();
    }
  }, [articleId]); // <-- ¡Aquí está la clave! Solo 'articleId' como dependencia

  const loadArticle = async () => {
    if (!articleId) return;
    try {
      setLoading(true);
      const articleData = await apiService.getArticle(articleId);
      setArticle(articleData);
      console.log("Article data:", articleData);
      console.log("Image URL:", articleData?.image_url); // Añadido para depurar la URL de la imagen
      setEditedContent((articleData?.body ?? '') as string);
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al cargar el artículo' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveChanges = async () => {
    if (!article) return;

    try {
      setSaving(true);
      setAlert(null);
      
      await apiService.updateArticle(article.id, {
        body: editedContent,
      });
      
      setAlert({ type: 'success', message: 'Cambios guardados exitosamente' });
      
      // Update the local article state
      if (article) {
        setArticle(prev => prev ? { ...prev, body: editedContent } : null);
      }
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al guardar los cambios' });
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!article) return;

    try {
      setPublishing(true);
      setAlert(null);
      
      const result = await apiService.publishArticle(article.id);
      
      setAlert({ 
        type: 'success', 
        message: `Artículo publicado exitosamente. Archivo: ${result.filename || 'generado'}` 
      });
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al publicar el artículo' });
    } finally {
      setPublishing(false);
    }
  };

  const handleGenerateSuggestions = async () => {
    if (!article) return;

    try {
      setGeneratingSuggestions(true);
      setAlert(null);
      setSuggestions([]);
      setSelectedSuggestions(new Set());
      
      const response = await apiService.generateSuggestions(article.id);
      
      // Parse suggestions from plain text
      const suggestionsList = response.suggestions
        .split('\n')
        .filter(line => line.trim().length > 0)
        .map(line => line.replace(/^[-•*]\s*/, '').trim())
        .filter(suggestion => suggestion.length > 0);
      
      setSuggestions(suggestionsList);
      
      if (suggestionsList.length === 0) {
        setAlert({ type: 'info', message: 'No se generaron sugerencias en este momento' });
      }
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al generar sugerencias' });
    } finally {
      setGeneratingSuggestions(false);
    }
  };

  const toggleSuggestionSelection = (index: number) => {
    const newSelected = new Set(selectedSuggestions);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedSuggestions(newSelected);
  };

  const handleApplySuggestions = async () => {
    if (!article || selectedSuggestions.size === 0) return;

    try {
      setApplyingSuggestions(true);
      setAlert(null);
      
      const selectedSuggestionTexts = Array.from(selectedSuggestions)
        .map(index => suggestions[index])
        .filter(Boolean);
      
      const instruction = `Aplica estas sugerencias:\n${selectedSuggestionTexts.map(s => `- ${s}`).join('\n')}`;
      
      const response = await apiService.rewriteArticle(
        article?.id,
        editedContent,
        instruction
      );
      
      setEditedContent(response.rewritten_text);
      setSelectedSuggestions(new Set());
      
      setAlert({ type: 'success', message: 'Sugerencias aplicadas exitosamente' });
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al aplicar las sugerencias' });
    } finally {
      setApplyingSuggestions(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
        return dateString; // This line seems to be a mistake, it will return the raw string
    if (isNaN(date.getTime())) {
        return 'Fecha inválida';
    }
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Cargando artículo..." />
      </div>
    );
  }

  if (!articleId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Artículo no especificado</p>
        <button
          onClick={onBack}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Volver a la lista
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        <div className="px-6 py-4 bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBack}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                  <Edit3 className="h-6 w-6 mr-3 text-purple-600" />
                  {article?.title}
                </h1>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Target className="h-4 w-4 mr-1" />
                    <span className="font-medium">Tema:</span> {article?.tema}
                  </div>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-1" />
                    {article?.created_at ? formatDate(article.created_at) : ''}
                  </div>
                  {article?.sources_score && (
                    <div className="flex items-center">
                      <span className="font-medium">Score:</span> {article.sources_score}/10
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {alert && (
        <div className="mb-6">
          <Alert type={alert.type} message={alert.message} onClose={() => setAlert(null)} />
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Editor */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Editor de Contenido</h2>
            </div>
            
            <div className="p-6">
              {/* Image Preview */}
              {article?.image_url && (
                <div className="mb-6">
                  <img
                    src={article.image_url}
                    alt={article.image_caption || article?.title}
                    className="w-full max-h-96 object-contain rounded-lg"
                  />
                  {article.image_caption && (
                    <p className="text-sm text-gray-600 text-center mt-2 italic">
                      {article.image_caption}
                    </p>
                  )}
                </div>
              )}
              {/* Content Editor */}
              <div className="space-y-4">
                <textarea
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  className="w-full h-96 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none font-mono text-sm"
                  placeholder="El contenido del artículo aparecerá aquí..."
                />
                
                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleSaveChanges}
                    disabled={saving || editedContent === article?.body}
                    className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {saving ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    <span className="ml-2">
                      {saving ? 'Guardando...' : 'Guardar Cambios'}
                    </span>
                  </button>
                  <button
                    onClick={handlePublish}
                    disabled={publishing}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {publishing ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    <span className="ml-2">
                      {publishing ? 'Publicando...' : 'Publicar Artículo'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* Suggestions Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Sparkles className="h-5 w-5 mr-2 text-purple-600" />
                Sugerencias del Copiloto
              </h2>
            </div>
            
            <div className="p-6">
              <div className="space-y-4">
                <button
                  onClick={handleGenerateSuggestions}
                  disabled={generatingSuggestions}
                  className="w-full flex items-center justify-center px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {generatingSuggestions ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Wand2 className="h-4 w-4" />
                  )}
                  <span className="ml-2">
                    {generatingSuggestions ? 'Generando...' : 'Generar Sugerencias'}
                  </span>
                </button>
                {selectedSuggestions.size > 0 && (
                  <button
                    onClick={handleApplySuggestions}
                    disabled={applyingSuggestions}
                    className="w-full flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {applyingSuggestions ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <CheckSquare className="h-4 w-4" />
                    )}
                    <span className="ml-2">
                      {applyingSuggestions 
                        ? 'Aplicando...' 
                        : `Aplicar ${selectedSuggestions.size} Seleccionada${selectedSuggestions.size !== 1 ? 's' : ''}`
                      }
                    </span>
                  </button>
                )}
                {/* Suggestions List */}
                {suggestions.length > 0 ? (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      Selecciona las sugerencias que deseas aplicar:
                    </h3>
                    {suggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        onClick={() => toggleSuggestionSelection(index)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          selectedSuggestions.has(index)
                            ? 'border-purple-300 bg-purple-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start space-x-2">
                          {selectedSuggestions.has(index) ? (
                            <CheckSquare className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                          ) : (
                            <Square className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                          )}
                          <p className="text-sm text-gray-700 leading-relaxed">
                            {suggestion}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Sparkles className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-sm">
                      Genera sugerencias clicando el botón de arriba para mejorar tu artículo con IA
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewArticle;
