import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 dark:from-gray-900 dark:to-gray-800">
      <nav className="flex justify-between items-center p-6 max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-orange-600">🍽️ MenuBox AI</h1>
        <div className="space-x-4">
          <Link to="/login" className="text-gray-600 hover:text-orange-600 dark:text-gray-300">
            Login
          </Link>
          <Link to="/register" className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition">
            Get Started
          </Link>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 dark:text-white mb-6">
            Never Order the Wrong Thing Again
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Upload a menu or tell us the restaurant. We'll analyze reviews and recommend 
            the best dishes based on your preferences.
          </p>
          <Link to="/register" className="inline-block bg-orange-500 text-white text-lg px-8 py-4 rounded-xl hover:bg-orange-600 transition shadow-lg">
            Start Getting Better Recommendations →
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <div className="text-3xl mb-4">📸</div>
            <h3 className="text-xl font-semibold mb-2 dark:text-white">Snap a Menu</h3>
            <p className="text-gray-600 dark:text-gray-400">
              Upload a photo of any menu and we'll extract all the items instantly.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <div className="text-3xl mb-4">⭐</div>
            <h3 className="text-xl font-semibold mb-2 dark:text-white">Review Analysis</h3>
            <p className="text-gray-600 dark:text-gray-400">
              We aggregate reviews from Yelp, Google, and more to find the crowd favorites.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm">
            <div className="text-3xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2 dark:text-white">Personalized Picks</h3>
            <p className="text-gray-600 dark:text-gray-400">
              AI matches top dishes to your taste preferences and dietary needs.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Home;
