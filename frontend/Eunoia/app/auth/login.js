// app/auth/login.js
// Changes from original:
//   • Calls POST /auth/register  then navigates to OTP screen
//   • Calls POST /auth/login via AuthContext.login()
//   • Shows server error messages (wrong password, unverified, etc.)
//   • Loading state on button

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, KeyboardAvoidingView, Platform, ScrollView,
  ActivityIndicator, Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Eye, EyeOff, Mail, Lock, User as UserIcon } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { useAuth } from '../../src/context/AuthContext';
import { register } from '../../src/api/auth';


export default function AuthScreen() {
  const router = useRouter();
  const { login } = useAuth();

  const [isLogin,       setIsLogin]       = useState(true);
  const [showPassword,  setShowPassword]  = useState(false);
  const [loading,       setLoading]       = useState(false);

  const [fullName,  setFullName]  = useState('');
  const [email,     setEmail]     = useState('');
  const [password,  setPassword]  = useState('');

  const handleAuth = async () => {
    if (!email || !password) {
      Alert.alert('Missing fields', 'Please fill in all fields.');
      return;
    }
    setLoading(true);
    try {
      if (isLogin) {
        // ── Login path ────────────────────────────────────────────────────
        await login(email, password);
      } else {
        // ── Register path → navigate to OTP screen ─────────────────────
        if (!fullName) { Alert.alert('Missing fields', 'Please enter your name.'); return; }
        await register({ full_name: fullName, email, password });
        // Pass email to OTP screen via query param
        router.push({ pathname: '/auth/otp', params: { email } });
      }
    }  catch (err) {
      let errorMessage = 'Something went wrong. Please try again.';

       if (err.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Your server may be slow or the ngrok tunnel may have expired. Please try again.';
        } else if (!err.response) {

        errorMessage = 'Could not reach the server. Please check your internet connection.';
      } else {
        const status = err.response.status;
        const detail = err.response.data?.detail;
 
        if (status === 401) {
          errorMessage = 'Incorrect email or password. Please try again.';
        } else if (status === 403) {
          errorMessage = 'Your account is not verified. Please check your email for the OTP code.';
        } else if (status === 409) {
          errorMessage = 'An account with this email already exists.';
        } else if (status === 422) {
          errorMessage = 'Please enter a valid email address.';
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again in a moment.';
        }
      }
  
        Alert.alert(isLogin ? 'Login Failed' : 'Registration Failed', errorMessage);
      } finally {
        setLoading(false);
      }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.header}>
            <Text style={styles.title}>{isLogin ? 'Welcome Back' : 'Create Account'}</Text>
            <Text style={styles.subtitle}>
              {isLogin
                ? 'Sign in to continue your wellness journey'
                : 'Join Eunoia and start tracking your peace'}
            </Text>
          </View>

          <View style={styles.form}>
            {!isLogin && (
              <View style={styles.inputContainer}>
                <UserIcon color={COLORS.text} size={20} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Full Name"
                  placeholderTextColor="#999"
                  value={fullName}
                  onChangeText={setFullName}
                />
              </View>
            )}

            <View style={styles.inputContainer}>
              <Mail color={COLORS.text} size={20} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Email Address"
                placeholderTextColor="#999"
                keyboardType="email-address"
                autoCapitalize="none"
                value={email}
                onChangeText={setEmail}
              />
            </View>

            <View style={styles.inputContainer}>
              <Lock color={COLORS.text} size={20} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Password"
                placeholderTextColor="#999"
                secureTextEntry={!showPassword}
                value={password}
                onChangeText={setPassword}
              />
              <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                {showPassword
                  ? <EyeOff color={COLORS.text} size={20} />
                  : <Eye     color={COLORS.text} size={20} />}
              </TouchableOpacity>
            </View>

            <TouchableOpacity 
              onPress={() => router.push({
                pathname: '/screens/change-password',
                params: { email: email } // Pre-fill the email if they typed it
              })}
              style={styles.forgotPasswordContainer}
            >
              <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.mainButton, loading && { opacity: 0.7 }]}
              onPress={handleAuth}
              disabled={loading}
            >
              {loading
                ? <ActivityIndicator color="white" />
                : <Text style={styles.mainButtonText}>{isLogin ? 'Login' : 'Sign Up'}</Text>}
            </TouchableOpacity>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
            </Text>
            <TouchableOpacity onPress={() => setIsLogin(!isLogin)}>
              <Text style={styles.toggleText}>{isLogin ? 'Register' : 'Login'}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: 30, flexGrow: 1, justifyContent: 'center' },
  header:        { marginBottom: 40 },
  title:         { fontSize: 32, fontWeight: 'bold', color: COLORS.text, marginBottom: 10 },
  subtitle:      { fontSize: 16, color: COLORS.text, opacity: 0.6, lineHeight: 22 },
  form:          { width: '100%' },
  inputContainer: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: COLORS.card, borderRadius: 20,
    paddingHorizontal: 20, paddingVertical: Platform.OS === 'ios' ? 15 : 5,
    marginBottom: 15, elevation: 2,
    shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5,
  },
  inputIcon:      { marginRight: 15, opacity: 0.5 },
  input:          { flex: 1, color: COLORS.text, fontSize: 16 },
  mainButton: {
    backgroundColor: COLORS.primary, paddingVertical: 18,
    borderRadius: 20, alignItems: 'center', elevation: 3,
    shadowColor: COLORS.primary, shadowOpacity: 0.3, shadowRadius: 8,
    marginTop: 10,
  },
  forgotPasswordContainer: {
    alignSelf: 'flex-end',
    marginBottom: 20,
    marginRight: 5,
    marginTop: -5, // Pulls it slightly closer to the password field
  },
  forgotPasswordText: {
    color: COLORS.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  mainButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  footer:         { flexDirection: 'row', justifyContent: 'center', marginTop: 40 },
  footerText:     { color: COLORS.text, opacity: 0.6, fontSize: 15 },
  toggleText:     { color: COLORS.primary, fontWeight: 'bold', fontSize: 15 },
});