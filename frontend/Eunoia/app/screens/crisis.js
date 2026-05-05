// app/screens/crisis.js
// Changes from original:
//   • Loads GET /therapists → shows real emergency contacts + directory
//   • Emergency contacts (is_emergency_contact=true) shown as primary action buttons
//   • Rest of directory shown in a scrollable list below
//   • Linking.openURL(`tel:${number}`) still works the same

import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
  SafeAreaView, Linking, ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Phone, User, X } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { getTherapists } from '../../src/api/reports';

export default function CrisisScreen() {
  const router = useRouter();
  const [therapists,  setTherapists]  = useState([]);
  const [loading,     setLoading]     = useState(true);

  useEffect(() => {
    getTherapists()
      .then(({ data }) => setTherapists(data.therapists ?? []))
      .catch(() => {})   // fallback: show static content if API fails
      .finally(() => setLoading(false));
  }, []);

  const emergency = therapists.filter((t) => t.is_emergency_contact);
  const directory = therapists.filter((t) => !t.is_emergency_contact);

  const handleCall = (number) => Linking.openURL(`tel:${number}`);

  return (
    <SafeAreaView style={styles.container}>
      <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
        <X color={COLORS.text} size={28} />
      </TouchableOpacity>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.alertHeader}>
          <View style={styles.iconCircle}>
            <Phone color="white" size={40} />
          </View>
          <Text style={styles.title}>You're not alone.</Text>
          <Text style={styles.subtitle}>
            Help is available right now. Reach out to one of the resources below.
          </Text>
        </View>

        {loading ? (
          <ActivityIndicator color={COLORS.crisis} size="large" style={{ marginVertical: 30 }} />
        ) : (
          <>
            {/* Emergency contacts — one button each */}
            {emergency.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Crisis Lines — Available 24/7</Text>
                {emergency.map((t) => (
                  <TouchableOpacity
                    key={t.id}
                    style={styles.primaryAction}
                    onPress={() => handleCall(t.contact_number)}
                  >
                    <View style={styles.actionIcon}>
                      <Phone color="white" size={22} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.actionTitle}>{t.name}</Text>
                      <Text style={styles.actionSub}>{t.specialization}</Text>
                    </View>
                    <Text style={styles.actionNumber}>{t.contact_number}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Therapist directory */}
            {directory.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Therapist Directory</Text>
                {directory.map((t) => (
                  <TouchableOpacity
                    key={t.id}
                    style={styles.secondaryAction}
                    onPress={() => handleCall(t.contact_number)}
                  >
                    <User color={COLORS.crisis} size={22} />
                    <View style={styles.actionDetails}>
                      <Text style={styles.secondaryTitle}>{t.name}</Text>
                      <Text style={styles.secondarySub}>
                        {t.specialization} · {t.location}
                      </Text>
                    </View>
                    <Text style={styles.secondaryNumber}>{t.contact_number}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Fallback if API returned nothing */}
            {therapists.length === 0 && (
              <TouchableOpacity
                style={styles.primaryAction}
                onPress={() => handleCall('1166')}
              >
                <View style={styles.actionIcon}><Phone color="white" size={22} /></View>
                <View>
                  <Text style={styles.actionTitle}>National Helpline</Text>
                  <Text style={styles.actionSub}>Available 24/7 · Toll-free</Text>
                </View>
              </TouchableOpacity>
            )}
          </>
        )}

        {/* Grounding tip */}
        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>Quick Grounding Tip</Text>
          <Text style={styles.tipText}>
            Find 5 things you can see, 4 you can touch, 3 you can hear. Breathe slowly.
          </Text>
        </View>

        {/* Medical disclaimer (PRD §5) */}
        <Text style={styles.disclaimer}>
          Eunoia is not a substitute for professional medical advice, diagnosis, or treatment.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: COLORS.background },
  closeButton:  { padding: 20, alignSelf: 'flex-end' },
  content:      { paddingHorizontal: 25, alignItems: 'center', paddingBottom: 40 },
  alertHeader:  { alignItems: 'center', marginBottom: 30 },
  iconCircle: {
    width: 80, height: 80, borderRadius: 40,
    backgroundColor: COLORS.crisis, justifyContent: 'center', alignItems: 'center',
    marginBottom: 20, elevation: 5,
  },
  title:    { fontSize: 26, fontWeight: 'bold', color: COLORS.crisis, textAlign: 'center' },
  subtitle: { fontSize: 16, color: COLORS.text, opacity: 0.7, textAlign: 'center', marginTop: 8, lineHeight: 24 },
  section:  { width: '100%', marginBottom: 25 },
  sectionTitle: { fontSize: 14, fontWeight: 'bold', color: COLORS.text, opacity: 0.4, marginBottom: 12, textTransform: 'uppercase' },
  primaryAction: {
    backgroundColor: COLORS.crisis, flexDirection: 'row', width: '100%',
    padding: 18, borderRadius: 20, alignItems: 'center', marginBottom: 10, elevation: 2,
  },
  actionIcon:   { marginRight: 15, backgroundColor: 'rgba(255,255,255,0.2)', padding: 8, borderRadius: 12 },
  actionTitle:  { color: 'white', fontSize: 16, fontWeight: 'bold' },
  actionSub:    { color: 'white', opacity: 0.8, fontSize: 13 },
  actionNumber: { color: 'white', fontSize: 13, fontWeight: '600', opacity: 0.9 },
  secondaryAction: {
    flexDirection: 'row', backgroundColor: COLORS.card, padding: 16,
    borderRadius: 18, alignItems: 'center', marginBottom: 10,
    borderWidth: 1, borderColor: COLORS.crisis + '25',
  },
  actionDetails:   { flex: 1, marginLeft: 12 },
  secondaryTitle:  { fontSize: 15, fontWeight: '600', color: COLORS.text },
  secondarySub:    { fontSize: 12, color: COLORS.text, opacity: 0.5, marginTop: 2 },
  secondaryNumber: { fontSize: 13, color: COLORS.crisis, fontWeight: '600' },
  tipCard: {
    backgroundColor: COLORS.primary + '10', padding: 20, borderRadius: 20,
    width: '100%', borderStyle: 'dashed', borderWidth: 1, borderColor: COLORS.primary, marginBottom: 20,
  },
  tipTitle:   { fontSize: 15, fontWeight: 'bold', color: COLORS.primary, marginBottom: 5 },
  tipText:    { fontSize: 14, color: COLORS.text, lineHeight: 20, opacity: 0.8 },
  disclaimer: { fontSize: 11, color: COLORS.text, opacity: 0.35, textAlign: 'center', lineHeight: 16 },
});