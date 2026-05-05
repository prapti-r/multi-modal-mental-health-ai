import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, SafeAreaView, Alert, ActivityIndicator } from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { ChevronLeft, Lock } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { useAuth } from '../../src/context/AuthContext';

export default function ChangePasswordScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const { token } = useLocalSearchParams(); // Used if coming from a "Forgot Password" email link

  const [form, setForm] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [loading, setLoading] = useState(false);

  const handleUpdate = async () => {
    if (form.newPassword !== form.confirmPassword) {
      Alert.alert("Error", "Passwords do not match");
      return;
    }
    
    setLoading(true);
    try {
      // API Call logic here (e.g., updatePassword(form))
      Alert.alert("Success", "Password updated successfully", [
        { text: "OK", onPress: () => router.back() }
      ]);
    } catch (err) {
      Alert.alert("Error", "Failed to update password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <ChevronLeft color={COLORS.text} size={28} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{user ? "Change Password" : "Reset Password"}</Text>
        <View style={{ width: 28 }} /> 
      </View>

      <View style={styles.content}>
        {user && (
          <View style={styles.inputContainer}>
            <Text style={styles.label}>Current Password</Text>
            <TextInput 
              style={styles.input} 
              secureTextEntry 
              placeholder="Enter current password"
              onChangeText={(val) => setForm({...form, oldPassword: val})}
            />
          </View>
        )}

        <View style={styles.inputContainer}>
          <Text style={styles.label}>New Password</Text>
          <TextInput 
            style={styles.input} 
            secureTextEntry 
            placeholder="Minimum 8 characters"
            onChangeText={(val) => setForm({...form, newPassword: val})}
          />
        </View>

        <TouchableOpacity 
          style={styles.button} 
          onPress={handleUpdate}
          disabled={loading}
        >
          {loading ? <ActivityIndicator color="white" /> : <Text style={styles.buttonText}>Update Password</Text>}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  headerTitle: { fontSize: 18, fontWeight: 'bold', color: COLORS.text },
  content: { padding: 24 },
  inputContainer: { marginBottom: 20 },
  label: { fontSize: 14, color: COLORS.text, opacity: 0.6, marginBottom: 8 },
  input: { backgroundColor: COLORS.card, padding: 16, borderRadius: 12, color: COLORS.text, borderWidth: 1, borderColor: COLORS.gray },
  button: { backgroundColor: COLORS.primary, padding: 18, borderRadius: 12, alignItems: 'center', marginTop: 20 },
  buttonText: { color: 'white', fontWeight: 'bold', fontSize: 16 }
});