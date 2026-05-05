import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../src/constants/Theme';

export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* App Logo or Illustration Placeholder */}
        <View style={styles.imageContainer}>
           <Text style={styles.logoPlaceholder}>🌱</Text>
        </View>

        <Text style={styles.title}>Welcome to Eunoia</Text>
        <Text style={styles.subtitle}>
          Your companion for mental wellness.{"\n"}
          Let's start your journey to a calmer you.
        </Text>

        <TouchableOpacity
          style={styles.button}
          onPress={() => router.push('/auth/login')}
        >
          <Text style={styles.buttonText}>Get Started</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40
  },
  imageContainer: {
    width: 200,
    height: 200,
    borderRadius: 100,
    backgroundColor: COLORS.primary + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 40
  },
  logoPlaceholder: { fontSize: 80 },
  title: {
    fontSize: 34,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 15,
    textAlign: 'center'
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.text,
    opacity: 0.6,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 60
  },
  button: {
    backgroundColor: COLORS.primary,
    paddingVertical: 18,
    paddingHorizontal: 50,
    borderRadius: 30,
    elevation: 3,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold'
  }
});