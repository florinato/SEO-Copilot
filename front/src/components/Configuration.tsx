import { RefreshCw, Save, Settings } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { ConfigBase } from '../types/api';
import Alert from './Alert';
import LoadingSpinner from './LoadingSpinner';

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<ConfigBase>({
    longitud_texto: 1000,
    tono_texto: 'neutral',
    min_score_fuente: 7,
    num_fuentes_scraper: 10,
    num_resultados_scraper: 5,
    min_score_generador: 6,
    num_fuentes_generador: 3,
    num_imagenes_buscar: 2,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedTema, setSelectedTema] = useState('Defecto'); // TODO: Inicializar con el prompt del usuario
  const [alert, setAlert] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, [selectedTema]);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setAlert(null);
      const configData = await apiService.getConfig(selectedTema);
      setConfig(configData);
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al cargar la configuración' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setConfig(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 : value,
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setAlert(null);
      
      await apiService.updateConfig({
        tema: selectedTema,
        ...config,
      });
      
      setAlert({ type: 'success', message: 'Configuración guardada exitosamente' });
    } catch (error) {
      setAlert({ type: 'error', message: 'Error al guardar la configuración. Esta funcionalidad puede no estar implementada en el backend.' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setConfig({
      longitud_texto: 1000,
      tono_texto: 'neutral',
      min_score_fuente: 7,
      num_fuentes_scraper: 10,
      num_resultados_scraper: 5,
      min_score_generador: 6,
      num_fuentes_generador: 3,
      num_imagenes_buscar: 2,
    });
    setAlert({ type: 'info', message: 'Configuración restablecida a valores por defecto' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="Cargando configuración..." />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Settings className="h-6 w-6 mr-3 text-amber-600" />
            Configuración Global
          </h2>
          <p className="text-gray-600 mt-1">
            Ajusta los parámetros por defecto para la generación de artículos
          </p>
        </div>

        <div className="p-6">
          {alert && (
            <div className="mb-6">
              <Alert type={alert.type} message={alert.message} onClose={() => setAlert(null)} />
            </div>
          )}

          {/* Tema Selection */}
          <div className="mb-6">
            <label htmlFor="tema" className="block text-sm font-medium text-gray-700 mb-2">
              Tema de Configuración
            </label>
            <select
              id="tema"
              value={selectedTema}
              onChange={(e) => setSelectedTema(e.target.value)}
              className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            >
              <option value="Defecto">Defecto</option>
              <option value="Tecnologia">Tecnología</option>
              <option value="Salud">Salud</option>
              <option value="Negocios">Negocios</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Selecciona el tema para cargar/guardar configuraciones específicas
            </p>
          </div>

          <form className="space-y-6">
            {/* Configuración de Contenido */}
            <div className="border-b pb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Configuración de Contenido
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label htmlFor="longitud_texto" className="block text-sm font-medium text-gray-700 mb-2">
                    Longitud del Texto
                  </label>
                  <input
                    type="number"
                    id="longitud_texto"
                    name="longitud_texto"
                    value={config.longitud_texto}
                    onChange={handleInputChange}
                    min="100"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Número de palabras aproximado</p>
                </div>

                <div>
                  <label htmlFor="tono_texto" className="block text-sm font-medium text-gray-700 mb-2">
                    Tono del Texto
                  </label>
                  <select
                    id="tono_texto"
                    name="tono_texto"
                    value={config.tono_texto}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
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
                    value={config.num_imagenes_buscar}
                    onChange={handleInputChange}
                    min="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">0 para desactivar imágenes</p>
                </div>
              </div>
            </div>

            {/* Configuración de Fuentes */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Configuración de Fuentes
              </h3>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label htmlFor="min_score_fuente" className="block text-sm font-medium text-gray-700 mb-2">
                    Score Mínimo Fuente
                  </label>
                  <input
                    type="number"
                    id="min_score_fuente"
                    name="min_score_fuente"
                    value={config.min_score_fuente}
                    onChange={handleInputChange}
                    min="1"
                    max="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Calidad mínima de fuentes (1-10)</p>
                </div>

                <div>
                  <label htmlFor="num_fuentes_scraper" className="block text-sm font-medium text-gray-700 mb-2">
                    Buscar (Scraper)
                  </label>
                  <input
                    type="number"
                    id="num_fuentes_scraper"
                    name="num_fuentes_scraper"
                    value={config.num_fuentes_scraper}
                    onChange={handleInputChange}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Fuentes a buscar</p>
                </div>

                <div>
                  <label htmlFor="num_resultados_scraper" className="block text-sm font-medium text-gray-700 mb-2">
                    Analizar (Scraper)
                  </label>
                  <input
                    type="number"
                    id="num_resultados_scraper"
                    name="num_resultados_scraper"
                    value={config.num_resultados_scraper}
                    onChange={handleInputChange}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Resultados a analizar en detalle</p>
                </div>

                <div>
                  <label htmlFor="min_score_generador" className="block text-sm font-medium text-gray-700 mb-2">
                    Score Mínimo Usar
                  </label>
                  <input
                    type="number"
                    id="min_score_generador"
                    name="min_score_generador"
                    value={config.min_score_generador}
                    onChange={handleInputChange}
                    min="1"
                    max="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Score mínimo para usar en generación</p>
                </div>

                <div>
                  <label htmlFor="num_fuentes_generador" className="block text-sm font-medium text-gray-700 mb-2">
                    Usar (Generador)
                  </label>
                  <input
                    type="number"
                    id="num_fuentes_generador"
                    name="num_fuentes_generador"
                    value={config.num_fuentes_generador}
                    onChange={handleInputChange}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">Fuentes a usar para generación</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 pt-6 border-t">
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="flex items-center px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span className="ml-2">
                  {saving ? 'Guardando...' : 'Guardar Configuración'}
                </span>
              </button>

              <button
                type="button"
                onClick={loadConfig}
                disabled={loading}
                className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="ml-2">Recargar</span>
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="flex items-center px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-colors"
              >
                <Settings className="h-4 w-4" />
                <span className="ml-2">Restablecer</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Configuration;
