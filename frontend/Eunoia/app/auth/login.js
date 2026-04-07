import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, SafeAreaView, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useRouter } from 'expo-router';
import { Eye, EyeOff, Mail, Lock, User as UserIcon } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

export default function AuthScreen() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  // Form States
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');

  const handleAuth = () => {
    // For now, we just navigate to the Dashboard
    router.replace('/(tabs)/home');
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>{isLogin ? 'Welcome Back' : 'Create Account'}</Text>
            <Text style={styles.subtitle}>
              {isLogin ? 'Sign in to continue your wellness journey' : 'Join Eunoia and start tracking your peace'}
            </Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            {!isLogin && (
              <View style={styles.inputContainer}>
                <UserIcon color={COLORS.text} size={20} style={styles.inputIcon} />
                <TextInput
                  style={styles.input}
                  placeholder="Username"
                  placeholderTextColor="#999"
                  value={username}
                  onChangeText={setUsername}
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
                {showPassword ? <EyeOff color={COLORS.text} size={20} /> : <Eye color={COLORS.text} size={20} />}
              </TouchableOpacity>
            </View>

            {isLogin && (
              <TouchableOpacity style={styles.forgotButton}>
                <Text style={styles.forgotText}>Forgot Password?</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity style={styles.mainButton} onPress={handleAuth}>
              <Text style={styles.mainButtonText}>{isLogin ? 'Login' : 'Sign Up'}</Text>
            </TouchableOpacity>
          </View>

          {/* Toggle Login/Signup */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              {isLogin ? "Don't have an account? " : "Already have an account? "}
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
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: 30, flexGrow: 1, justifyContent: 'center' },
  header: { marginBottom: 40 },
  title: { fontSize: 32, fontWeight: 'bold', color: COLORS.text, marginBottom: 10 },
  subtitle: { fontSize: 16, color: COLORS.text, opacity: 0.6, lineHeight: 22 },

  form: { width: '100%' },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: Platform.OS === 'ios' ? 15 : 5,
    marginBottom: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
  },
  inputIcon: { marginRight: 15, opacity: 0.5 },
  input: { flex: 1, color: COLORS.text, fontSize: 16 },

  forgotButton: { alignSelf: 'flex-end', marginBottom: 30 },
  forgotText: { color: COLORS.secondary, fontWeight: '600' },

  mainButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 18,
    borderRadius: 20,
    alignItems: 'center',
    elevation: 3,
    shadowColor: COLORS.primary,
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  mainButtonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },

  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 40
  },
  footerText: { color: COLORS.text, opacity: 0.6, fontSize: 15 },
  toggleText: { color: COLORS.primary, fontWeight: 'bold', fontSize: 15 }
});