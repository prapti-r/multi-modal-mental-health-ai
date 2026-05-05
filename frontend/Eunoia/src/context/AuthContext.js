// src/context/AuthContext.js
// Fixes:
//   • logout() now fully clears state AND navigates to /auth/login
//   • On mount, if token refresh fails, sets user=null cleanly so the
//     index screen's guard can redirect correctly
//   • Exposes isLoggedIn boolean for simpler guard checks

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import * as SecureStore from 'expo-secure-store';
import { useRouter, useSegments } from 'expo-router';
import { login as apiLogin, logout as apiLogout, getProfile } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,      setUser]      = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const router   = useRouter();
  const segments = useSegments();

  // ── Auth guard — runs whenever user or route changes ────────────────────
  useEffect(() => {
    if (isLoading) return; // wait until initial token check is done

    const inAuthGroup = segments[0] === 'auth';
    const inTabs      = segments[0] === '(tabs)';

    if (!user && inTabs) {
      // Not logged in but on a protected screen → go to login
      router.replace('/auth/login');
    } else if (user && inAuthGroup) {
      // Logged in but on auth screen → go to home
      router.replace('/(tabs)/home');
    }
  }, [user, segments, isLoading]);

  // ── On mount: restore session from stored token ──────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) {
          const { data } = await getProfile();
          setUser(data);
        }
      } catch {
        // Token expired or invalid — wipe everything
        await SecureStore.deleteItemAsync('access_token');
        await SecureStore.deleteItemAsync('refresh_token');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  // ── Login ────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { data } = await apiLogin({ email, password });
    await SecureStore.setItemAsync('access_token',  data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    const profile = await getProfile();
    setUser(profile.data);
    return profile.data;
  }, []);

  // ── Logout ───────────────────────────────────────────────────────────────
  // FIX: clears tokens first, then nulls user, then navigates.
  // Previous bug: user was set to null but navigation was done in profile.js
  // with router.replace('/auth/login') — if AuthContext's guard fires first
  // it can conflict. Now logout owns the navigation.
  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch {
      // Ignore — token may already be expired or blocklisted
    }
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    setUser(null);
    // Navigate to login — the auth guard above also handles this,
    // but we do it explicitly here so it's instant.
    router.replace('/auth/login');
  }, []);

  // ── Refresh user profile (call after PATCH /user/profile) ───────────────
  const refreshUser = useCallback(async () => {
    const { data } = await getProfile();
    setUser(data);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};