import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import Constants from "expo-constants";

export const BASE_URL =
  Constants.expoConfig?.extra?.EXPO_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" ,
    'ngrok-skip-browser-warning': 'true',
  },
});

//  Request interceptor — attach Bearer token 
client.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

//  Response interceptor — refresh on 401 
let _isRefreshing = false;
/** @type {Array<{ resolve: (value: unknown) => void; reject: (reason?: any) => void }>} */
let _queue = [];

/**
 * Resolve/reject queued requests waiting on token refresh.
 * @param {Error | null} error
 * @param {string | null} token
 */
const processQueue = (error, token) => {
  _queue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)));
  _queue = [];
};


client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    if (_isRefreshing) {
      return new Promise((resolve, reject) => {
        _queue.push({ resolve, reject });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return client(original);
      });
    }

    original._retry = true;
    _isRefreshing = true;

    try {
      const refreshToken = await SecureStore.getItemAsync('refresh_token');
      if (!refreshToken) throw new Error('No refresh token');

      const { data } = await axios.post(`${BASE_URL}/auth/refresh`, null, {
        headers: { Authorization: `Bearer ${refreshToken}` },
      });

      await SecureStore.setItemAsync('access_token',  data.access_token);
      await SecureStore.setItemAsync('refresh_token', data.refresh_token);

      processQueue(null, data.access_token);
      original.headers.Authorization = `Bearer ${data.access_token}`;
      return client(original);
    } catch (err) {
      processQueue(err instanceof Error ? err : new Error('Token refresh failed'), null);
      // Wipe tokens — AuthContext listener will redirect to login
      await SecureStore.deleteItemAsync('access_token');
      await SecureStore.deleteItemAsync('refresh_token');
      return Promise.reject(err);
    } finally {
      _isRefreshing = false;
    }
  }
);

export default client;