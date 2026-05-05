// app/auth/otp.js  ← NEW FILE (does not exist yet)
// Shown after registration. Accepts the 6-digit OTP, calls POST /auth/verify-otp.
// On success → navigates to login. Includes resend link.

import React, { useRef, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { COLORS } from '../../src/constants/Theme';
import { verifyOtp, resendOtp } from '../../src/api/auth';

export default function OtpScreen() {
  const router = useRouter();
  const { email } = useLocalSearchParams();   // passed from register screen

  const [code,     setCode]     = useState(['', '', '', '', '', '']);
  const [loading,  setLoading]  = useState(false);
  const [resending, setResending] = useState(false);
  const inputs = useRef([]);

  const handleChange = (text, index) => {
    const updated = [...code];
    updated[index] = text.replace(/\D/g, '');   // digits only
    setCode(updated);
    // Auto-advance to next box
    if (text && index < 5) inputs.current[index + 1]?.focus();
  };

  const handleBackspace = (key, index) => {
    if (key === 'Backspace' && !code[index] && index > 0) {
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
      Alert.alert('Verified!', 'Your account is ready. Please log in.', [
        { text: 'OK', onPress: () => router.replace('/auth/login') },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Invalid or expired code.';
      Alert.alert('Error', detail);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    try {
     await resendOtp({ email });
      Alert.alert('Sent!', 'A new code has been sent to your email.');
    } catch (err) {
      Alert.alert('Error', 'Could not resend code. Please try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>Check your email</Text>
        <Text style={styles.subtitle}>
          We sent a 6-digit code to{'\n'}
          <Text style={styles.email}>{email}</Text>
        </Text>

        {/* OTP boxes */}
        <View style={styles.codeRow}>
          {code.map((digit, i) => (
            <TextInput
              key={i}
              ref={(r) => (inputs.current[i] = r)}
              style={[styles.codeBox, digit && styles.codeBoxFilled]}
              value={digit}
              onChangeText={(t) => handleChange(t, i)}
              onKeyPress={({ nativeEvent }) => handleBackspace(nativeEvent.key, i)}
              keyboardType="number-pad"
              maxLength={1}
              selectTextOnFocus
            />
          ))}
        </View>

        <TouchableOpacity
          style={[styles.button, loading && { opacity: 0.7 }]}
          onPress={handleVerify}
          disabled={loading}
        >
          {loading
            ? <ActivityIndicator color="white" />
            : <Text style={styles.buttonText}>Verify Account</Text>}
        </TouchableOpacity>

        <TouchableOpacity onPress={handleResend} disabled={resending} style={styles.resend}>
          <Text style={styles.resendText}>
            {resending ? 'Sending...' : "Didn't receive it? Resend code"}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content:   { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 30 },
  title:     { fontSize: 28, fontWeight: 'bold', color: COLORS.text, marginBottom: 12 },
  subtitle:  { fontSize: 16, color: COLORS.text, opacity: 0.6, textAlign: 'center', lineHeight: 24, marginBottom: 40 },
  email:     { color: COLORS.primary, fontWeight: '600' },
  codeRow:   { flexDirection: 'row', gap: 10, marginBottom: 40 },
  codeBox: {
    width: 48, height: 58, borderRadius: 14,
    backgroundColor: COLORS.card, textAlign: 'center',
    fontSize: 22, fontWeight: 'bold', color: COLORS.text,
    borderWidth: 2, borderColor: COLORS.gray,
    elevation: 2,
  },
  codeBoxFilled: { borderColor: COLORS.primary, backgroundColor: COLORS.primary + '10' },
  button: {
    backgroundColor: COLORS.primary, width: '100%',
    paddingVertical: 18, borderRadius: 20, alignItems: 'center',
    elevation: 3, marginBottom: 20,
  },
  buttonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  resend:     { marginTop: 10 },
  resendText: { color: COLORS.secondary, fontWeight: '600', fontSize: 15 },
});