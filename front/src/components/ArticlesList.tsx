import { Calendar, FileText, Search } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { GeneratedArticleSummary } from '../types/api';
import Alert from './Alert';
import LoadingSpinner from './LoadingSpinner';

import { useNavigate } from 'react-router-dom';

interface ArticlesListProps {
  refreshTrigger: number;
  onArticleSelect: (id: string) => void;
}

const ArticlesList: React.FC<ArticlesListProps> = ({ refreshTrigger, onArticleSelect }) => {
  const navigate = useNavigate();
  const [articles, setArticles] = useState<GeneratedArticleSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [alert, setAlert] = useState<{ type: 'error' | 'info'; message: string } | null>(null);

  useEffect(() => {
    loadArticles();
  }, [refreshTrigger]);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setAlert(null);
      const articlesList = await apiService.getArticles();
      setArticles(articlesList);
      
      if (articlesList.length === 0) {
        setAlert({ type: 'info', message: 'No hay artículos generados aún. ¡Crea tu primer artículo!' });
      }
    } catch (error) {
      setAlert({ 
        type: 'error', 
        message: 'Error al cargar los artículos. Verifica que el backend esté ejecutándose.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredArticles = articles.filter(article =>
    article.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    article.tema?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-emerald-50 to-teal-50 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <FileText className="h-6 w-6 mr-3 text-emerald-600" />
                Artículos Generados
              </h2>
              <p className="text-gray-600 mt-1">
                {articles.length} artículo{articles.length !== 1 ? 's' : ''} en total
              </p>
            </div>
          </div>
        </div>
        <div className="p-6">
          {/* Barra de búsqueda */}
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por título o tema..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>
          {/* Contenido */}
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" text="Cargando artículos..." />
            </div>
          ) : alert ? (
            <Alert type={alert.type} message={alert.message} onClose={() => setAlert(null)} />
          ) : filteredArticles.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'No se encontraron artículos' : 'No hay artículos'}
              </h3>
              <p className="text-gray-500">
                {searchTerm
                  ? 'Intenta con diferentes términos de búsqueda'
                  : 'Comienza generando tu primer artículo'}
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {filteredArticles.map((article) => (
                <div
                  key={article.id}
                  onClick={() => {
                    onArticleSelect(String(article.id));
                    navigate(`/review/${article.id}`);
                  }}
                  className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md hover:border-emerald-300 cursor-pointer transition-all duration-200 group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors line-clamp-2">
                        {article.title}
                      </h3>
                      <p className="text-sm text-gray-500 mb-1">
                        <span className="font-medium">Tema:</span> {article.tema}
                      </p>
                      <p className="text-sm text-gray-400 flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        {formatDate(article.created_at)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticlesList;
