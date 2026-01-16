import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { menuAPI, recommendationsAPI } from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const [restaurantName, setRestaurantName] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Upload form state
  const [uploadName, setUploadName] = useState('');
  const [uploadLocation, setUploadLocation] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  
  // Refs for file inputs
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

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
      const restaurantRes = await menuAPI.searchRestaurant(restaurantName, location);
      const restaurant = restaurantRes.data;
      const recRes = await recommendationsAPI.generate(restaurant.id);
      navigate(`/results/${recRes.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles(prev => [...prev, ...files]);
    }
  };

  const handleCameraCapture = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFiles(prev => [...prev, file]);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;
    
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      
      // Append all files
      selectedFiles.forEach((file, index) => {
        formData.append('files', file);
      });
      
      if (uploadName.trim()) {
        formData.append('restaurant_name', uploadName.trim());
      }
      if (uploadLocation.trim()) {
        formData.append('location', uploadLocation.trim());
      }
      
      const uploadRes = await menuAPI.uploadImages(formData);
      const { restaurant_id } = uploadRes.data;
      
      // Generate recommendations (will use OCR-only mode)
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
            <h2 className="text-xl font-semibold mb-4 dark:text-white">📸 Upload Menu Photos</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Take photos or upload images of the menu pages. Inputting the restaurant name and location helps us find reviews online!
            </p>
            <form onSubmit={handleFileUpload} className="space-y-3">
              {/* Camera and File buttons */}
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-orange-300 dark:border-orange-700 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition disabled:opacity-50"
                >
                  <span>📷</span>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Take Photo</span>
                </button>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition disabled:opacity-50"
                >
                  <span>📁</span>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Browse Files</span>
                </button>
              </div>

              {/* Hidden file inputs */}
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleCameraCapture}
                className="hidden"
              />
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                className="hidden"
              />

              {/* Selected files preview */}
              {selectedFiles.length > 0 && (
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {selectedFiles.length} photo{selectedFiles.length > 1 ? 's' : ''} selected
                    </span>
                    <button
                      type="button"
                      onClick={clearAllFiles}
                      className="text-sm text-red-500 hover:text-red-700"
                    >
                      Clear all
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="relative group bg-gray-100 dark:bg-gray-700 rounded-lg p-2 pr-8"
                      >
                        <span className="text-sm text-gray-600 dark:text-gray-300 truncate max-w-[150px] block">
                          {file.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-red-500"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <input
                type="text"
                value={uploadName}
                onChange={(e) => setUploadName(e.target.value)}
                placeholder="Restaurant name (optional)"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
              />
              
              <input
                type="text"
                value={uploadLocation}
                onChange={(e) => setUploadLocation(e.target.value)}
                placeholder="Location (optional, helps find reviews)"
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
              />
              
              <button 
                type="submit"
                disabled={loading || selectedFiles.length === 0}
                className="w-full bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition disabled:opacity-50"
              >
                {loading ? 'Processing...' : `Get Recommendations${selectedFiles.length > 0 ? ` (${selectedFiles.length} photo${selectedFiles.length > 1 ? 's' : ''})` : ''}`}
              </button>
            </form>
          </div>

          {/* Search Restaurant */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-4 dark:text-white">🔍 Search Restaurant</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Enter the restaurant name to look up their menu online.
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
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              {selectedFiles.length > 0 
                ? 'Reading menu photos and generating recommendations...' 
                : 'Analyzing menu and generating recommendations...'}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;