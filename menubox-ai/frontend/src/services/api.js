import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
};

export const userAPI = {
  getMe: () => api.get('/user/me'),
  getPreferences: () => api.get('/user/preferences'),
  updatePreferences: (data) => api.put('/user/preferences', data),
};

export const menuAPI = {
  // Single file upload (legacy)
  uploadImage: (formData) => api.post('/menu/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  // Multiple file upload
  uploadImages: (formData) => api.post('/menu/upload-multiple', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  searchRestaurant: (name, location) => api.post('/menu/search', { name, location }),
  getRestaurant: (id) => api.get(`/menu/${id}`),
};

export const recommendationsAPI = {
  generate: (restaurantId, maxItems = 5) => api.post('/recommendations/generate', {
    restaurant_id: restaurantId,
    max_items: maxItems,
  }),
  getById: (id) => api.get(`/recommendations/${id}`),
  list: (limit = 10) => api.get(`/recommendations/?limit=${limit}`),
};

export default api;