import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let accessToken = localStorage.getItem('token');
let refreshToken = localStorage.getItem('refreshToken');

const setTokens = (access, refresh) => {
  accessToken = access;
  refreshToken = refresh;
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
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
};

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
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

    // If 401 and we have a refresh token, try to refresh
    if (error.response?.status === 401 && refreshToken && !originalRequest._retry) {
      if (isRefreshing) {
        // Wait for the refresh to complete
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
          refresh_token: refreshToken,
        });

        const newAccessToken = response.data.access_token;
        setTokens(newAccessToken, refreshToken);
        
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

    // If 403 (unverified email), redirect to verification page
    if (error.response?.status === 403) {
      const detail = error.response?.data?.detail || '';
      if (detail.includes('verify your email')) {
        // Store email for resend functionality
        window.location.href = '/login?unverified=true';
        return Promise.reject(error);
      }
    }

    // If still 401 after refresh attempt, redirect to login
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
    setTokens(response.data.access_token, response.data.refresh_token);
    return response;
  },
  login: async (data) => {
    const response = await api.post('/auth/login', data);
    setTokens(response.data.access_token, response.data.refresh_token);
    return response;
  },
  logout: async () => {
    try {
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } finally {
      clearTokens();
    }
  },
  logoutAll: () => api.post('/auth/logout-all'),
  refresh: (token) => api.post('/auth/refresh', { refresh_token: token }),
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { 
    token, 
    new_password: newPassword 
  }),
  changePassword: (currentPassword, newPassword) => api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  }),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  resendVerification: (email) => api.post('/auth/resend-verification', { email }),
  getMe: () => api.get('/auth/me'),
  
  // Session management
  getSessions: () => api.get('/auth/sessions'),
  revokeSession: (sessionId) => api.delete(`/auth/sessions/${sessionId}`),
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

// Export helper to check auth status
export const isAuthenticated = () => !!accessToken;
export const getAccessToken = () => accessToken;
export const getRefreshToken = () => refreshToken;
export { clearTokens, setTokens };

export default api;