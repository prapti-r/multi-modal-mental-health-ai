// app/screens/edit-profile.js
// Lets the user update their full_name and profile picture.
// Calls PATCH /user/profile. Updates AuthContext on success.

import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  SafeAreaView, KeyboardAvoidingView, Platform,
  ActivityIndicator, Alert, ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { ChevronLeft, Camera, User, Save } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { useAuth } from '../../src/context/AuthContext';
import { updateProfile } from '../../src/api/auth';
import { Image } from 'react-native';

export default function EditProfileScreen() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();

  const [fullName,   setFullName]   = useState(user?.full_name ?? '');
  const [avatarUri,  setAvatarUri]  = useState(user?.profile_image_url ?? null);
  const [loading,    setLoading]    = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleNameChange = (val) => {
    setFullName(val);
    setHasChanges(val !== user?.full_name || avatarUri !== user?.profile_image_url);
  };

  const handlePickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Photo library access is required to change your avatar.');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.7,
    });
    if (!result.canceled) {
      setAvatarUri(result.assets[0].uri);
      setHasChanges(true);
    }
  };

  const handleSave = async () => {
    if (!fullName.trim()) {
      Alert.alert('Required', 'Name cannot be empty.');
      return;
    }
    setLoading(true);
    try {
      await updateProfile({
        full_name:        fullName.trim(),
        profile_image_url: avatarUri ?? undefined,
      });
      await refreshUser();
      Alert.alert('Saved', 'Your profile has been updated.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err) {
      const detail = err?.response?.data?.detail ?? 'Could not save profile. Please try again.';
      Alert.alert('Error', detail);
    } finally {
      setLoading(false);
    }
  };

  const initials = fullName.trim()
    ? fullName.trim().split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <ChevronLeft color={COLORS.text} size={28} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Edit Profile</Text>
          <TouchableOpacity
            style={[styles.saveBtn, { opacity: hasChanges && !loading ? 1 : 0.4 }]}
            onPress={handleSave}
            disabled={!hasChanges || loading}
          >
            {loading
              ? <ActivityIndicator color="white" size="small" />
              : <Save color="white" size={18} />}
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          {/* Avatar */}
          <TouchableOpacity style={styles.avatarWrap} onPress={handlePickImage}>
            <View style={styles.avatar}>
              {avatarUri ?
                (<Image source={{ uri: avatarUri }} style={styles.avatarImg} /> 
                ) : (
                <Text style={styles.avatarInitials}>{initials}</Text>
                )}
            </View>
            <View style={styles.cameraBadge}>
              <Camera color="white" size={16} />
            </View>
            <Text style={styles.changePhotoText}>Change photo</Text>
          </TouchableOpacity>

          {/* Fields */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Full Name</Text>
            <View style={styles.inputRow}>
              <User color={COLORS.text} size={18} style={{ opacity: 0.4 }} />
              <TextInput
                style={styles.input}
                value={fullName}
                onChangeText={handleNameChange}
                placeholder="Your full name"
                placeholderTextColor="#999"
                autoCapitalize="words"
              />
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Email</Text>
            <View style={[styles.inputRow, styles.inputRowDisabled]}>
              <TextInput
                style={[styles.input, { opacity: 0.45 }]}
                value={user?.email ?? ''}
                editable={false}
              />
            </View>
            <Text style={styles.fieldNote}>Email cannot be changed here.</Text>
          </View>

          {/* Verified badge */}
          {user?.is_verified && (
            <View style={styles.verifiedRow}>
              <Text style={styles.verifiedText}>✓ Verified account</Text>
            </View>
          )}

          {/* Save button (large) */}
          <TouchableOpacity
            style={[styles.saveButton, { opacity: hasChanges && !loading ? 1 : 0.45 }]}
            onPress={handleSave}
            disabled={!hasChanges || loading}
          >
            {loading
              ? <ActivityIndicator color="white" />
              : <Text style={styles.saveButtonText}>Save Changes</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: COLORS.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  backBtn:     { padding: 4 },
  headerTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text },
  saveBtn: {
    backgroundColor: COLORS.primary, padding: 10,
    borderRadius: 12, width: 40, alignItems: 'center',
  },
  content:      { paddingHorizontal: 24, paddingBottom: 40 },
  avatarWrap:   { alignItems: 'center', marginVertical: 28 },
  avatar: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: COLORS.secondary,
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 8,
  },
  avatarInitials:  { fontSize: 36, fontWeight: 'bold', color: 'white' },
  avatarImg:       { width: 100, height: 100, borderRadius: 50 },
  cameraBadge: {
    position: 'absolute', bottom: 36, right: '50%',
    transform: [{ translateX: 30 }],
    backgroundColor: COLORS.primary, padding: 8, borderRadius: 14,
    borderWidth: 3, borderColor: COLORS.background,
  },
  changePhotoText: { fontSize: 14, color: COLORS.primary, fontWeight: '600' },
  section:       { marginBottom: 20 },
  sectionLabel: {
    fontSize: 13, fontWeight: '600', color: COLORS.text,
    opacity: 0.5, textTransform: 'uppercase', letterSpacing: 0.5,
    marginBottom: 8, marginLeft: 4,
  },
  inputRow: {
    flexDirection: 'row', alignItems: 'center', gap: 12,
    backgroundColor: COLORS.card, borderRadius: 18,
    paddingHorizontal: 18, paddingVertical: Platform.OS === 'ios' ? 16 : 8,
    borderWidth: 1, borderColor: COLORS.gray,
  },
  inputRowDisabled: { opacity: 0.6 },
  input:        { flex: 1, fontSize: 16, color: COLORS.text },
  fieldNote:    { fontSize: 12, color: COLORS.text, opacity: 0.35, marginTop: 6, marginLeft: 4 },
  verifiedRow:  { marginBottom: 16 },
  verifiedText: { fontSize: 13, color: COLORS.primary, fontWeight: '600' },
  saveButton: {
    backgroundColor: COLORS.primary, paddingVertical: 18,
    borderRadius: 20, alignItems: 'center', marginTop: 10,
    elevation: 3, shadowColor: COLORS.primary, shadowOpacity: 0.25, shadowRadius: 8,
  },
  saveButtonText: { color: 'white', fontSize: 17, fontWeight: 'bold' },
});
