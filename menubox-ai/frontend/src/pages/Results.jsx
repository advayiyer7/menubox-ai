import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { recommendationsAPI } from '../services/api';

function Results() {
  const { id } = useParams();
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRecommendation = async () => {
      try {
        const res = await recommendationsAPI.getById(id);
        setRecommendation(res.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load recommendation');
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecommendation();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading recommendations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Link to="/dashboard" className="text-orange-600 hover:text-orange-700">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-2xl font-bold text-orange-600">
            🍽️ MenuBox AI
          </Link>
          <Link to="/dashboard" className="text-gray-600 hover:text-orange-600 dark:text-gray-300">
            ← Back to Dashboard
          </Link>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Your Recommendations
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Based on review analysis and your preferences
        </p>

        <div className="space-y-4">
          {recommendation?.recommended_items?.map((item, index) => (
            <div 
              key={index}
              className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm flex items-start gap-4"
            >
              <div className="flex-shrink-0 w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center text-orange-600 dark:text-orange-300 font-bold text-lg">
                #{index + 1}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-xl font-semibold dark:text-white">{item.item_name}</h3>
                  <span className={`text-sm px-2 py-0.5 rounded-full ${
                    item.score >= 90 
                      ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                      : item.score >= 70
                      ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                  }`}>
                    {item.score}% match
                  </span>
                </div>
                <p className="text-gray-600 dark:text-gray-400">{item.reasoning}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <Link 
            to="/dashboard"
            className="inline-block bg-orange-500 text-white px-6 py-3 rounded-lg hover:bg-orange-600 transition"
          >
            Try Another Restaurant
          </Link>
        </div>
      </main>
    </div>
  );
}

export default Results;
