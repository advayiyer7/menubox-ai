import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { userAPI } from '../services/api';

const DIETARY_OPTIONS = [
  'Vegetarian',
  'Vegan', 
  'Gluten-Free',
  'Dairy-Free',
  'Halal',
  'Kosher',
  'Nut-Free',
  'Shellfish-Free',
  'Low-Carb',
  'Keto'
];

const CUISINE_OPTIONS = [
  'Italian',
  'Japanese',
  'Mexican',
  'Indian',
  'Chinese',
  'Thai',
  'Vietnamese',
  'Korean',
  'French',
  'Mediterranean',
  'American',
  'Greek',
  'Spanish',
  'Middle Eastern'
];

const SPICE_LEVELS = [
  { value: 'none', label: '🚫 No Spice' },
  { value: 'mild', label: '🌶️ Mild' },
  { value: 'medium', label: '🌶️🌶️ Medium' },
  { value: 'hot', label: '🌶️🌶️🌶️ Hot' },
  { value: 'extra_hot', label: '🔥 Extra Hot' }
];

const PRICE_OPTIONS = [
  { value: 'budget', label: '$ Budget' },
  { value: 'moderate', label: '$$ Moderate' },
  { value: 'upscale', label: '$$$ Upscale' },
  { value: 'any', label: '💰 Any Price' }
];

function Preferences() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [preferences, setPreferences] = useState({
    dietary_restrictions: [],
    favorite_cuisines: [],
    disliked_ingredients: [],
    spice_preference: 'medium',
    price_preference: 'any',
    custom_notes: ''
  });
  
  const [newIngredient, setNewIngredient] = useState('');

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const res = await userAPI.getPreferences();
      setPreferences({
        dietary_restrictions: res.data.dietary_restrictions || [],
        favorite_cuisines: res.data.favorite_cuisines || [],
        disliked_ingredients: res.data.disliked_ingredients || [],
        spice_preference: res.data.spice_preference || 'medium',
        price_preference: res.data.price_preference || 'any',
        custom_notes: res.data.custom_notes || ''
      });
    } catch (err) {
      setError('Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      await userAPI.updatePreferences(preferences);
      setSuccess('Preferences saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const toggleDietary = (option) => {
    const lower = option.toLowerCase();
    setPreferences(prev => ({
      ...prev,
      dietary_restrictions: prev.dietary_restrictions.includes(lower)
        ? prev.dietary_restrictions.filter(d => d !== lower)
        : [...prev.dietary_restrictions, lower]
    }));
  };

  const toggleCuisine = (cuisine) => {
    const lower = cuisine.toLowerCase();
    setPreferences(prev => ({
      ...prev,
      favorite_cuisines: prev.favorite_cuisines.includes(lower)
        ? prev.favorite_cuisines.filter(c => c !== lower)
        : [...prev.favorite_cuisines, lower]
    }));
  };

  const addDislikedIngredient = () => {
    if (!newIngredient.trim()) return;
    const lower = newIngredient.trim().toLowerCase();
    if (!preferences.disliked_ingredients.includes(lower)) {
      setPreferences(prev => ({
        ...prev,
        disliked_ingredients: [...prev.disliked_ingredients, lower]
      }));
    }
    setNewIngredient('');
  };

  const removeDislikedIngredient = (ingredient) => {
    setPreferences(prev => ({
      ...prev,
      disliked_ingredients: prev.disliked_ingredients.filter(i => i !== ingredient)
    }));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-orange-500 border-t-transparent"></div>
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
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-gray-600 hover:text-orange-600 dark:text-gray-300">
              Dashboard
            </Link>
            <button onClick={handleLogout} className="text-gray-600 hover:text-orange-600 dark:text-gray-300">
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            ⚙️ Your Preferences
          </h1>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-orange-500 text-white px-6 py-2 rounded-lg hover:bg-orange-600 transition disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg">
            {success}
          </div>
        )}

        <div className="space-y-8">
          {/* Dietary Restrictions */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">🥗 Dietary Restrictions</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Select any dietary restrictions we should consider.
            </p>
            <div className="flex flex-wrap gap-2">
              {DIETARY_OPTIONS.map(option => (
                <button
                  key={option}
                  onClick={() => toggleDietary(option)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    preferences.dietary_restrictions.includes(option.toLowerCase())
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>

          {/* Favorite Cuisines */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">🌍 Favorite Cuisines</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Select cuisines you enjoy (helps us recommend dishes you'll love).
            </p>
            <div className="flex flex-wrap gap-2">
              {CUISINE_OPTIONS.map(cuisine => (
                <button
                  key={cuisine}
                  onClick={() => toggleCuisine(cuisine)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    preferences.favorite_cuisines.includes(cuisine.toLowerCase())
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {cuisine}
                </button>
              ))}
            </div>
          </div>

          {/* Disliked Ingredients */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">🚫 Disliked Ingredients</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Add ingredients you'd like us to avoid recommending.
            </p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newIngredient}
                onChange={(e) => setNewIngredient(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addDislikedIngredient()}
                placeholder="e.g., cilantro, mushrooms..."
                className="flex-1 px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <button
                onClick={addDislikedIngredient}
                className="bg-gray-200 dark:bg-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {preferences.disliked_ingredients.map(ingredient => (
                <span
                  key={ingredient}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-full text-sm"
                >
                  {ingredient}
                  <button
                    onClick={() => removeDislikedIngredient(ingredient)}
                    className="hover:text-red-900 dark:hover:text-red-200"
                  >
                    ×
                  </button>
                </span>
              ))}
              {preferences.disliked_ingredients.length === 0 && (
                <span className="text-gray-400 dark:text-gray-500 text-sm">No ingredients added yet</span>
              )}
            </div>
          </div>

          {/* Spice Preference */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">🌶️ Spice Preference</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              How much spice can you handle?
            </p>
            <div className="flex flex-wrap gap-2">
              {SPICE_LEVELS.map(level => (
                <button
                  key={level.value}
                  onClick={() => setPreferences(prev => ({ ...prev, spice_preference: level.value }))}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    preferences.spice_preference === level.value
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>

          {/* Price Preference */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">💰 Price Preference</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              What's your typical budget for a meal?
            </p>
            <div className="flex flex-wrap gap-2">
              {PRICE_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => setPreferences(prev => ({ ...prev, price_preference: option.value }))}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition ${
                    preferences.price_preference === option.value
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Custom Notes */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <h2 className="text-xl font-semibold mb-2 dark:text-white">📝 Additional Preferences</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Anything else we should know? (e.g., "absolutely no beef", "prefer grilled over fried", "looking for healthy options")
            </p>
            <textarea
              value={preferences.custom_notes}
              onChange={(e) => setPreferences(prev => ({ ...prev, custom_notes: e.target.value }))}
              placeholder="Enter any additional preferences or notes..."
              rows={4}
              maxLength={500}
              className="w-full px-4 py-3 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white resize-none"
            />
            <p className="text-sm text-gray-400 mt-2 text-right">
              {preferences.custom_notes.length}/500 characters
            </p>
          </div>
        </div>

        {/* Bottom Save Button */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-orange-500 text-white px-8 py-3 rounded-lg hover:bg-orange-600 transition disabled:opacity-50 font-semibold"
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </main>
    </div>
  );
}

export default Preferences;