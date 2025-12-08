import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Helper function to check if token is expired
const isTokenExpired = (token) => {
    if (!token) return true;

    try {
        const decoded = jwtDecode(token);
        const currentTime = Date.now() / 1000;
        // Check if token expires in less than 1 minute (buffer for network delay)
        return decoded.exp < (currentTime + 60);
    } catch (error) {
        return true;
    }
};

// Helper function to get token expiration time in milliseconds
const getTokenExpiration = (token) => {
    if (!token) return null;

    try {
        const decoded = jwtDecode(token);
        return decoded.exp * 1000; // Convert to milliseconds
    } catch (error) {
        return null;
    }
};

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add response interceptor to handle 401 errors and auto-refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken && !isTokenExpired(refreshToken)) {
                    // Try to refresh the access token
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken
                    });

                    const { access_token } = response.data;
                    localStorage.setItem('access_token', access_token);

                    // Retry the original request with new token
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed, logout user
                authAPI.logout();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    register: async (email, password) => {
        const response = await api.post('/auth/register', { email, password });
        // Store tokens after successful registration
        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        return response.data;
    },

    login: async (email, password) => {
        const response = await api.post('/auth/login', { email, password });
        // Store tokens after successful login
        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    isAuthenticated: () => {
        const token = localStorage.getItem('access_token');
        // Check if token exists AND is not expired
        return token && !isTokenExpired(token);
    },

    getTokenExpiration: () => {
        const token = localStorage.getItem('access_token');
        return getTokenExpiration(token);
    },

    refreshToken: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken || isTokenExpired(refreshToken)) {
            throw new Error('Refresh token expired');
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);
        return access_token;
    }
};

// Chat API
export const chatAPI = {
    sendMessage: async (query, sessionId = null) => {
        const payload = { query };
        if (sessionId) {
            payload.session_id = sessionId;
        }
        const response = await api.post('/chat', payload);
        return response.data;
    }
};

export default api;

