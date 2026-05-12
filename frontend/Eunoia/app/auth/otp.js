import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, ActivityIndicator, Alert,
  KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { COLORS } from '../../src/constants/Theme';
import { verifyOtp, resendOtp, login } from '../../src/api/auth';
import * as SecureStore from 'expo-secure-store';
import { useAuth } from '../../src/context/AuthContext';

export default function OtpScreen() {
  const router      = useRouter();
  const { email, password }   = useLocalSearchParams(); // password passed from register if available
  const { login: ctxLogin }   = useAuth();

  const [code,      setCode]      = useState(['', '', '', '', '', '']);
  const [loading,   setLoading]   = useState(false);
  const [resending, setResending] = useState(false);
  const inputs = useRef([]);

  // Auto-focus first box on mount
  useEffect(() => {
    setTimeout(() => inputs.current[0]?.focus(), 300);
  }, []);

  const handleChange = (text, index) => {
    const digit = text.replace(/\D/g, '').slice(-1); // digits only, 1 char
    const updated = [...code];
    updated[index] = digit;
    setCode(updated);
    if (digit && index < 5) inputs.current[index + 1]?.focus();
  };

  const handleBackspace = (key, index) => {
    if (key === 'Backspace' && !code[index] && index > 0) {
      const updated = [...code];
      updated[index - 1] = '';
      setCode(updated);
      inputs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const fullCode = code.join('');
    if (fullCode.length < 6) {
      Alert.alert('Incomplete', 'Please enter the full 6-digit code.');
      return;
    }
    setLoading(true);
    try {
      await verifyOtp({ email, code: fullCode });

      if (password) {
        try {
          await ctxLogin(email, password);
          // AuthContext auth guard will navigate to /(tabs)/home automatically
          return;
        } catch {
          // Auto-login failed (rare) — fall back to manual login
        }
      }

      // No password available — send to login with a success message
      Alert.alert('Account verified!', 'Please sign in to continue.', [
        { text: 'OK', onPress: () => router.replace('/auth/login') },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Invalid or expired code. Please try again.';
      Alert.alert('Verification failed', detail);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    try {
      await resendOtp({ email });
      Alert.alert('Code sent!', 'A new 6-digit code has been sent to your email.');
      setCode(['', '', '', '', '', '']);
      setTimeout(() => inputs.current[0]?.focus(), 200);
    } catch {
      Alert.alert('Error', 'Could not resend the code. Please try again in a moment.');
    } finally {
      setResending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* KeyboardAvoidingView + ScrollView together ensure the button is
          always reachable even when the number keyboard is open */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.title}>Check your email</Text>
          <Text style={styles.subtitle}>
            We sent a 6-digit code to{'\n'}
            <Text style={styles.emailHighlight}>{email}</Text>
          </Text>

          {/* OTP input boxes */}
          <View style={styles.codeRow}>
            {code.map((digit, i) => (
              <TextInput
                key={i}
                ref={(r) => (inputs.current[i] = r)}
                style={[styles.codeBox, digit ? styles.codeBoxFilled : null]}
                value={digit}
                onChangeText={(t) => handleChange(t, i)}
                onKeyPress={({ nativeEvent }) => handleBackspace(nativeEvent.key, i)}
                keyboardType="number-pad"
                maxLength={1}
                selectTextOnFocus
                returnKeyType="done"
              />
            ))}
          </View>

          {/* Verify button — always visible because ScrollView handles keyboard */}
          <TouchableOpacity
            style={[styles.button, loading && { opacity: 0.7 }]}
            onPress={handleVerify}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color="white" />
              : <Text style={styles.buttonText}>Verify Account</Text>}
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleResend}
            disabled={resending}
            style={styles.resendBtn}
          >
            <Text style={styles.resendText}>
              {resending ? 'Sending new code…' : "Didn't receive it? Resend code"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Text style={styles.backText}>← Change email</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.background },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 30,
    paddingVertical: 40,
  },
  title:           { fontSize: 28, fontWeight: 'bold', color: COLORS.text, marginBottom: 12, textAlign: 'center' },
  subtitle:        { fontSize: 16, color: COLORS.text, opacity: 0.6, textAlign: 'center', lineHeight: 24, marginBottom: 40 },
  emailHighlight:  { color: COLORS.primary, fontWeight: '600', opacity: 1 },
  codeRow:         { flexDirection: 'row', gap: 10, marginBottom: 40 },
  codeBox: {
    width: 48, height: 58, borderRadius: 14,
    backgroundColor: COLORS.card, textAlign: 'center',
    fontSize: 22, fontWeight: 'bold', color: COLORS.text,
    borderWidth: 2, borderColor: COLORS.gray, elevation: 2,
  },
  codeBoxFilled:   { borderColor: COLORS.primary, backgroundColor: COLORS.primary + '12' },
  button: {
    backgroundColor: COLORS.primary, width: '100%',
    paddingVertical: 18, borderRadius: 20, alignItems: 'center',
    elevation: 3, marginBottom: 20,
    shadowColor: COLORS.primary, shadowOpacity: 0.25, shadowRadius: 8,
  },
  buttonText:      { color: 'white', fontSize: 18, fontWeight: 'bold' },
  resendBtn:       { marginBottom: 16, padding: 8 },
  resendText:      { color: COLORS.secondary, fontWeight: '600', fontSize: 15 },
  backBtn:         { padding: 8 },
  backText:        { color: COLORS.text, opacity: 0.4, fontSize: 14 },
});