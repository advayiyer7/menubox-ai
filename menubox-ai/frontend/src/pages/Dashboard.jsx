import { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { menuAPI, recommendationsAPI, authAPI } from '../services/api';

function Dashboard() {
  const navigate = useNavigate();
  const [restaurantName, setRestaurantName] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [uploadName, setUploadName] = useState('');
  const [uploadLocation, setUploadLocation] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

  const handleLogout = () => {
    authAPI.logout();
    navigate('/login', { replace: true });
    window.location.reload();
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
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;
    
    setLoading(true);
    setError('');
    
    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => formData.append('files', file));
      if (uploadName.trim()) formData.append('restaurant_name', uploadName.trim());
      if (uploadLocation.trim()) formData.append('location', uploadLocation.trim());
      
      const uploadRes = await menuAPI.uploadImages(formData);
      const recRes = await recommendationsAPI.generate(uploadRes.data.restaurant_id);
      navigate(`/results/${recRes.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process menu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Mobile-friendly nav */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <Link to="/dashboard" className="text-xl sm:text-2xl font-bold text-orange-600">
            🍽️ <span className="hidden xs:inline">MenuBox AI</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            <Link 
              to="/preferences" 
              className="p-2 text-gray-600 hover:text-orange-600 dark:text-gray-300"
              title="Preferences"
            >
              <span className="text-lg">⚙️</span>
              <span className="hidden sm:inline ml-1">Preferences</span>
            </Link>
            <button 
              onClick={handleLogout} 
              className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-300 text-sm sm:text-base"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-12">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Get Recommendations
        </h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-6 sm:mb-8">
          Set your <Link to="/preferences" className="text-orange-500 hover:underline">dietary preferences</Link> for personalized results.
        </p>

        {error && (
          <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="grid gap-4 sm:gap-6 md:grid-cols-2">
          {/* Upload Menu - Primary on mobile */}
          <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-sm order-1">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 dark:text-white flex items-center gap-2">
              📸 Upload Menu
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {isMobile ? 'Take a photo or upload menu images.' : 'Upload images of the menu.'}
            </p>
            
            <form onSubmit={handleFileUpload} className="space-y-3">
              {/* Camera + File buttons */}
              <div className="grid grid-cols-2 gap-2">
                {isMobile && (
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    disabled={loading}
                    className="flex flex-col items-center justify-center gap-1 p-4 border-2 border-dashed border-orange-300 dark:border-orange-700 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/20 transition disabled:opacity-50"
                  >
                    <span className="text-2xl">📷</span>
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">Camera</span>
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={loading}
                  className={`flex flex-col items-center justify-center gap-1 p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition disabled:opacity-50 ${!isMobile ? 'col-span-2' : ''}`}
                >
                  <span className="text-2xl">📁</span>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {isMobile ? 'Gallery' : 'Choose Files'}
                  </span>
                </button>
              </div>

              {/* Hidden inputs */}
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handleFileSelect}
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

              {/* Selected files */}
              {selectedFiles.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {selectedFiles.length} photo{selectedFiles.length > 1 ? 's' : ''}
                    </span>
                    <button
                      type="button"
                      onClick={clearAllFiles}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-1 bg-white dark:bg-gray-600 rounded px-2 py-1 text-xs"
                      >
                        <span className="truncate max-w-[80px] text-gray-600 dark:text-gray-300">
                          {file.name}
                        </span>
                        <button
                          type="button"
                          onClick={() => removeFile(index)}
                          className="text-gray-400 hover:text-red-500 ml-1"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Optional fields - collapsible on mobile */}
              <details className="group">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
                  + Add restaurant details (optional)
                </summary>
                <div className="mt-2 space-y-2">
                  <input
                    type="text"
                    value={uploadName}
                    onChange={(e) => setUploadName(e.target.value)}
                    placeholder="Restaurant name"
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
                  />
                  <input
                    type="text"
                    value={uploadLocation}
                    onChange={(e) => setUploadLocation(e.target.value)}
                    placeholder="City/Location"
                    className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
                  />
                </div>
              </details>
              
              <button 
                type="submit"
                disabled={loading || selectedFiles.length === 0}
                className="w-full bg-orange-500 text-white px-4 py-3 rounded-lg font-medium hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Processing...
                  </span>
                ) : (
                  `Get Recommendations${selectedFiles.length > 0 ? ` (${selectedFiles.length})` : ''}`
                )}
              </button>
            </form>
          </div>

          {/* Search Restaurant */}
          <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-sm order-2">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 dark:text-white flex items-center gap-2">
              🔍 Search Restaurant
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Find menu online by restaurant name.
            </p>
            
            <form onSubmit={handleSearch} className="space-y-3">
              <input
                type="text"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
                placeholder="Restaurant name..."
                className="w-full px-3 py-2 sm:py-2.5 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm sm:text-base"
              />
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="City or area (optional)..."
                className="w-full px-3 py-2 sm:py-2.5 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm sm:text-base"
              />
              <button 
                type="submit"
                disabled={loading || !restaurantName.trim()}
                className="w-full bg-orange-500 text-white px-4 py-3 rounded-lg font-medium hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    Searching...
                  </span>
                ) : (
                  'Search Menu'
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Loading overlay for mobile */}
        {loading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 md:hidden">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 mx-4 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-orange-500 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-300">
                {selectedFiles.length > 0 ? 'Reading menu...' : 'Finding menu...'}
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;