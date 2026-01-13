import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { menuAPI, recommendationsAPI } from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const [restaurantName, setRestaurantName] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!restaurantName.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Search for restaurant
      const restaurantRes = await menuAPI.searchRestaurant(restaurantName, location);
      const restaurant = restaurantRes.data;
      
      // Generate recommendations
      const recRes = await recommendationsAPI.generate(restaurant.id);
      
      // Navigate to results
      navigate(`/results/${recRes.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadRes = await menuAPI.uploadImage(formData);
      const { restaurant_id } = uploadRes.data;
      
      // Generate recommendations
      const recRes = await recommendationsAPI.generate(restaurant_id);
      
      navigate(`/results/${recRes.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process menu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-2xl font-bold text-orange-600">
            🍽️ MenuBox AI
          </Link>
          <div className="flex items-center gap-4">
            <Link 
              to="/preferences" 
              className="text-gray-600 hover:text-orange-600 dark:text-gray-300 flex items-center gap-1"
            >
              ⚙️ Preferences
            </Link>
            <button onClick={handleLogout} className="text-gray-600 hover:text-orange-600 dark:text-gray-300">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Get Menu Recommendations
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Set your <Link to="/preferences" className="text-orange-500 hover:underline">dietary preferences</Link> for personalized recommendations.
        </p>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {/* Upload Menu */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">📸 Upload Menu Photo</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Take a photo of the menu and we'll extract the items.
            </p>
            <label className="block">
              <input 
                type="file" 
                accept="image/*"
                onChange={handleFileUpload}
                disabled={loading}
                className="block w-full text-sm text-gray-500 dark:text-gray-400
                  file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0
                  file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700
                  hover:file:bg-orange-100 dark:file:bg-orange-900 dark:file:text-orange-300
                  disabled:opacity-50"
              />
            </label>
          </div>

          {/* Search Restaurant */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">🔍 Search Restaurant</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Enter the restaurant name to look up their menu.
            </p>
            <form onSubmit={handleSearch} className="space-y-3">
              <input
                type="text"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
                placeholder="Restaurant name..."
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Location (optional)..."
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <button 
                type="submit"
                disabled={loading || !restaurantName.trim()}
                className="w-full bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition disabled:opacity-50"
              >
                {loading ? 'Searching...' : 'Get Recommendations'}
              </button>
            </form>
          </div>
        </div>

        {loading && (
          <div className="mt-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-orange-500 border-t-transparent"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Analyzing menu and generating recommendations...</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;