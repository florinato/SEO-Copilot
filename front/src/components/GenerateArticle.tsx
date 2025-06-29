import React, { useState, useEffect } from 'react';
import { Send, Settings } from 'lucide-react';
import { apiService } from '../services/api';
import { ConfigBase, GenerateRequestModel } from '../types/api';
import LoadingSpinner from './LoadingSpinner';
import Alert from './Alert';

interface GenerateArticleProps {
  onArticleGenerated: () => void;
}

const GenerateArticle: React.FC<GenerateArticleProps> = ({ onArticleGenerated }) => {
  const [formData, setFormData] = useState<GenerateRequestModel>({
    tema: '',
    longitud_texto: 1000,
    tono_texto: 'neutral',
    min_score_fuente: 7,
    num_fuentes_scraper: 10,
    num_resultados_scraper: 5,
    min_score_generador: 6,
    num_fuentes_generador: 3,
    num_imagenes_buscar: 2,
  });

  const [loading, setLoading] = useState(false);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [alert, setAlert] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    loadDefaultConfig();
  }, []);

  const loadDefaultConfig = async () => {
    try {
      setLoadingConfig(true);
      const config = await apiService.getConfig('Defecto');
      setFormData(prev => ({ ...prev, ...config }));
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al cargar la configuración por defecto' });
    } finally {
      setLoadingConfig(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.tema.trim()) {
      setAlert({ type: 'error', message: 'El tema es obligatorio' });
      return;
    }

    setLoading(true);
    setAlert(null);

    try {
      const result = await apiService.generateArticle(formData);
      setAlert({ 
        type: 'success', 
        message: `Artículo generado exitosamente. ID: ${result.article_id}` 
      });
      setFormData(prev => ({ ...prev, tema: '' }));
      onArticleGenerated();
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: 'Error al generar el artículo. Verifica que el backend esté ejecutándose.' 
      });
    } finally {
      setLoading(false);
    }
  };

  if (loadingConfig) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Cargando configuración..." />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Send className="h-6 w-6 mr-3 text-blue-600" />
            Generar Nuevo Artículo
          </h2>
          <p className="text-gray-600 mt-1">Configura los parámetros para generar contenido optimizado para SEO</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {alert && (
            <Alert 
              type={alert.type} 
              message={alert.message} 
              onClose={() => setAlert(null)} 
            />
          )}

          {/* Tema Principal */}
          <div className="bg-blue-50 rounded-lg p-4">
            <label htmlFor="tema" className="block text-sm font-semibold text-gray-900 mb-2">
              Tema del Artículo *
            </label>
            <input
              type="text"
              id="tema"
              name="tema"
              value={formData.tema}
              onChange={handleInputChange}
              placeholder="Ej: Avances de la IA en medicina 2025"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          {/* Configuración de Contenido */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <label htmlFor="longitud_texto" className="block text-sm font-medium text-gray-700 mb-2">
                Longitud del Texto
              </label>
              <input
                type="number"
                id="longitud_texto"
                name="longitud_texto"
                value={formData.longitud_texto}
                onChange={handleInputChange}
                min="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="tono_texto" className="block text-sm font-medium text-gray-700 mb-2">
                Tono del Texto
              </label>
              <select
                id="tono_texto"
                name="tono_texto"
                value={formData.tono_texto}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="neutral">Neutral</option>
                <option value="formal">Formal</option>
                <option value="informal">Informal</option>
                <option value="técnico">Técnico</option>
              </select>
            </div>

            <div>
              <label htmlFor="num_imagenes_buscar" className="block text-sm font-medium text-gray-700 mb-2">
                Número de Imágenes
              </label>
              <input
                type="number"
                id="num_imagenes_buscar"
                name="num_imagenes_buscar"
                value={formData.num_imagenes_buscar}
                onChange={handleInputChange}
                min="0"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Configuración de Fuentes */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Settings className="h-5 w-5 mr-2 text-gray-600" />
              Configuración de Fuentes
            </h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label htmlFor="min_score_fuente" className="block text-sm font-medium text-gray-700 mb-2">
                  Score Mínimo Fuente
                </label>
                <input
                  type="number"
                  id="min_score_fuente"
                  name="min_score_fuente"
                  value={formData.min_score_fuente}
                  onChange={handleInputChange}
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="num_fuentes_scraper" className="block text-sm font-medium text-gray-700 mb-2">
                  Buscar (Scraper)
                </label>
                <input
                  type="number"
                  id="num_fuentes_scraper"
                  name="num_fuentes_scraper"
                  value={formData.num_fuentes_scraper}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="num_resultados_scraper" className="block text-sm font-medium text-gray-700 mb-2">
                  Analizar (Scraper)
                </label>
                <input
                  type="number"
                  id="num_resultados_scraper"
                  name="num_resultados_scraper"
                  value={formData.num_resultados_scraper}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="min_score_generador" className="block text-sm font-medium text-gray-700 mb-2">
                  Score Mínimo Usar
                </label>
                <input
                  type="number"
                  id="min_score_generador"
                  name="min_score_generador"
                  value={formData.min_score_generador}
                  onChange={handleInputChange}
                  min="1"
                  max="10"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="mt-4">
              <label htmlFor="num_fuentes_generador" className="block text-sm font-medium text-gray-700 mb-2">
                Usar (Generador)
              </label>
              <input
                type="number"
                id="num_fuentes_generador"
                name="num_fuentes_generador"
                value={formData.num_fuentes_generador}
                onChange={handleInputChange}
                min="1"
                className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Botón de Envío */}
          <div className="border-t pt-6">
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg shadow-md hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {loading ? (
                <div className="flex items-center">
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Generando Artículo...</span>
                </div>
              ) : (
                <div className="flex items-center">
                  <Send className="h-5 w-5 mr-2" />
                  Iniciar Generación
                </div>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GenerateArticle;