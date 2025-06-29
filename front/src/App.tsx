import { useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import ArticlesList from './components/ArticlesList.tsx';
import Configuration from './components/Configuration';
import GenerateArticle from './components/GenerateArticle';
import Navigation from './components/Navigation';
import ReviewArticle from './components/ReviewArticle';

function App() {
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleArticleGenerated = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<GenerateArticle onArticleGenerated={handleArticleGenerated} />} />
            <Route
              path="/articles"
              element={
                <ArticlesList
                  refreshTrigger={refreshTrigger}
                  onArticleSelect={id => setSelectedArticleId(Number(id))}
                />
              }
            />
            <Route path="/review/:id" element={<ReviewArticle articleId={Number(selectedArticleId)} onBack={() => {}} />} />
            <Route path="/config" element={<Configuration />} />
          </Routes>
        </main>
        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 mt-16">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <p className="text-center text-sm text-gray-500">
              SEO-Copilot Dashboard - Generación de contenido optimizado con IA
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
