import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Switch, Alert, ActivityIndicator, Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { User, Lock, Bell, ShieldCheck, LogOut, ChevronRight, Camera } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { useAuth } from '../../src/context/AuthContext';
import { updateSettings } from '../../src/api/auth';

export default function ProfileScreen() {
  const router             = useRouter();
  const { user, logout }   = useAuth();

  // FIX: initialise from real user settings, not hardcoded true
  const [notifications, setNotifications] = useState(
    user?.settings?.notifications_enabled ?? true
  );
  const [loggingOut, setLoggingOut] = useState(false);

  const handleNotificationToggle = async (val) => {
    setNotifications(val);
    try {
      await updateSettings({ notifications_enabled: val });
    } catch {
      setNotifications(!val); // revert on failure
      Alert.alert('Error', 'Could not update notification preference.');
    }
  };

  const handleLogout = () => {
    Alert.alert('Log Out', 'Are you sure you want to log out?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log Out',
        style: 'destructive',
        onPress: async () => {
          setLoggingOut(true);
          try {
            await logout(); // AuthContext.logout() now handles navigation
          } finally {
            setLoggingOut(false);
          }
        },
      },
    ]);
  };

  const SettingItem = ({ icon: IconComponent, title, subtitle, onPress, isSwitch, value, onToggle }) => (
    <TouchableOpacity style={styles.settingRow} onPress={onPress} disabled={isSwitch}>
      <View style={styles.settingIconContainer}>
        <IconComponent color={COLORS.primary} size={22} />
      </View>
      <View style={styles.settingTextContainer}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {isSwitch ? (
        <Switch
          value={value}
          onValueChange={onToggle}
          trackColor={{ false: COLORS.gray, true: COLORS.primary }}
        />
      ) : (
        <ChevronRight color={COLORS.text} size={20} opacity={0.3} />
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              {user?.profile_image_url ? (
                <Image 
                  source={{ uri: user.profile_image_url }} 
                  style={styles.avatarImg} 
                />
              ) : (
                <User color="white" size={50} />
              )}
            </View>
            <TouchableOpacity style={styles.editBadge}
            onPress={() => router.push('/screens/edit-profile')}>
              <Camera color="white" size={16} />
            </TouchableOpacity>
          </View>
          <Text style={styles.userName}>{user?.full_name ?? '—'}</Text>
          <Text style={styles.userEmail}>{user?.email ?? '—'}</Text>
          {user?.is_verified && (
            <View style={styles.verifiedBadge}>
              <Text style={styles.verifiedText}>✓ Verified</Text>
            </View>
          )}
        </View>

        {/* Account Section */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Account Settings</Text>
          <View style={styles.card}>
            <SettingItem
              icon={User}
              title="Edit Profile"
              subtitle="Change your name or avatar"
              onPress={() => router.push('/screens/edit-profile')}
            />
            <SettingItem
              icon={Lock}
              title="Change Password"
              onPress={() => router.push('/screens/change-password')}
            />
          </View>
        </View>

        {/* Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>Preferences</Text>
          <View style={styles.card}>
            <SettingItem
              icon={Bell}
              title="Notifications"
              isSwitch
              value={notifications}
              onToggle={handleNotificationToggle}
            />
            <SettingItem
              icon={ShieldCheck}
              title="Privacy Settings"
              subtitle="Manage your data and AI history"
              onPress={() => {}}
            />
          </View>
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} disabled={loggingOut}>
          {loggingOut
            ? <ActivityIndicator color={COLORS.crisis} />
            : <>
                <LogOut color={COLORS.crisis} size={22} />
                <Text style={styles.logoutText}>Logout</Text>
              </>}
        </TouchableOpacity>

        <Text style={styles.versionText}>Eunoia v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: 25 },
  profileHeader: { alignItems: 'center', marginVertical: 30 },
  avatarContainer: { position: 'relative', marginBottom: 15 },
  avatar: {
    width: 100, height: 100, borderRadius: 50,
    backgroundColor: COLORS.secondary, justifyContent: 'center', alignItems: 'center', elevation: 4, overflow: 'hidden',
  },
  avatarImg: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  editBadge: {
    position: 'absolute', bottom: 0, right: 0,
    backgroundColor: COLORS.primary, padding: 8, borderRadius: 15,
    borderWidth: 3, borderColor: COLORS.background,
  },
  userName:    { fontSize: 24, fontWeight: 'bold', color: COLORS.text },
  userEmail:   { fontSize: 14, color: COLORS.text, opacity: 0.5, marginTop: 4 },
  verifiedBadge: {
    marginTop: 8, backgroundColor: COLORS.primary + '20',
    paddingHorizontal: 12, paddingVertical: 4, borderRadius: 10,
  },
  verifiedText: { fontSize: 12, color: COLORS.primary, fontWeight: '600' },
  section:      { marginBottom: 25 },
  sectionLabel: {
    fontSize: 14, fontWeight: 'bold', color: COLORS.text,
    opacity: 0.4, marginLeft: 10, marginBottom: 10, textTransform: 'uppercase',
  },
  card: { backgroundColor: COLORS.card, borderRadius: 24, overflow: 'hidden', elevation: 2 },
  settingRow: {
    flexDirection: 'row', alignItems: 'center', padding: 18,
    borderBottomWidth: 1, borderBottomColor: COLORS.background,
  },
  settingIconContainer: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: COLORS.primary + '15', justifyContent: 'center', alignItems: 'center', marginRight: 15,
  },
  settingTextContainer: { flex: 1 },
  settingTitle:         { fontSize: 16, fontWeight: '600', color: COLORS.text },
  settingSubtitle:      { fontSize: 12, color: COLORS.text, opacity: 0.5, marginTop: 2 },
  logoutButton: {
    flexDirection: 'row', backgroundColor: COLORS.card, padding: 18,
    borderRadius: 20, justifyContent: 'center', alignItems: 'center',
    marginTop: 10, borderWidth: 1, borderColor: COLORS.crisis + '20',
  },
  logoutText:  { color: COLORS.crisis, fontWeight: 'bold', marginLeft: 10, fontSize: 16 },
  versionText: { textAlign: 'center', marginTop: 30, opacity: 0.2, fontSize: 12 },
});