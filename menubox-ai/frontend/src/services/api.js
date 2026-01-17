import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
const getStoredTokens = () => ({
  access: localStorage.getItem('token'),
  refresh: localStorage.getItem('refreshToken')
});

const setTokens = (access, refresh) => {
  if (access) {
    localStorage.setItem('token', access);
  } else {
    localStorage.removeItem('token');
  }
  if (refresh) {
    localStorage.setItem('refreshToken', refresh);
  } else {
    localStorage.removeItem('refreshToken');
  }
};

const clearTokens = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
};

// Add auth token to requests
api.interceptors.request.use((config) => {
  const { access } = getStoredTokens();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// Handle 401 errors and token refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const { refresh } = getStoredTokens();

    // If 401 and we have a refresh token, try to refresh
    if (error.response?.status === 401 && refresh && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refresh,
        });

        const newAccessToken = response.data.access_token;
        setTokens(newAccessToken, refresh);
        
        processQueue(null, newAccessToken);
        
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // If still 401, clear and redirect
    if (error.response?.status === 401) {
      clearTokens();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: async (data) => {
    const response = await api.post('/auth/register', data);
    // Don't store tokens - user must verify first
    return response;
  },
  login: async (data) => {
    const response = await api.post('/auth/login', data);
    setTokens(response.data.access_token, response.data.refresh_token);
    return response;
  },
  logout: () => {
    const { refresh } = getStoredTokens();
    clearTokens();
    if (refresh) {
      // Fire and forget - don't wait for response
      api.post('/auth/logout', { refresh_token: refresh }).catch(() => {});
    }
  },
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { 
    token, 
    new_password: newPassword 
  }),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
  getMe: () => api.get('/auth/me'),
};

export const userAPI = {
  getMe: () => api.get('/user/me'),
  getPreferences: () => api.get('/user/preferences'),
  updatePreferences: (data) => api.put('/user/preferences', data),
};

export const menuAPI = {
  uploadImage: (formData) => api.post('/menu/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
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

// Check if user is authenticated
export const isAuthenticated = () => {
  const { access } = getStoredTokens();
  return !!access;
};

export { clearTokens, setTokens };

export default api;