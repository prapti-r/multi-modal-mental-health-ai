import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, SafeAreaView, Linking } from 'react-native';
import { useRouter } from 'expo-router';
import { Phone, User, MessageSquare, X } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

export default function CrisisScreen() {
  const router = useRouter();

  const handleCall = (number) => {
    Linking.openURL(`tel:${number}`);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Close Button - because they might have clicked by mistake */}
      <TouchableOpacity style={styles.closeButton} onPress={() => router.back()}>
        <X color={COLORS.text} size={28} />
      </TouchableOpacity>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Warning Icon & Message */}
        <View style={styles.alertHeader}>
          <View style={styles.iconCircle}>
            <Phone color="white" size={40} />
          </View>
          <Text style={styles.title}>You’re not alone.</Text>
          <Text style={styles.subtitle}>
            It looks like you're going through a tough time. Help is available right now.
          </Text>
        </View>

        {/* Primary Action: Emergency Helpline */}
        <TouchableOpacity
          style={styles.primaryAction}
          onPress={() => handleCall('1166')} // Example Nepal Suicide Prevention Helpline
        >
          <View style={styles.actionIcon}>
            <Phone color="white" size={24} />
          </View>
          <View>
            <Text style={styles.actionTitle}>Call National Helpline</Text>
            <Text style={styles.actionSub}>Available 24/7 • Toll-free</Text>
          </View>
        </TouchableOpacity>

        {/* Secondary Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Other Support Options</Text>

          <TouchableOpacity style={styles.secondaryAction}>
            <User color={COLORS.crisis} size={24} />
            <View style={styles.actionDetails}>
              <Text style={styles.secondaryTitle}>Contact Your Therapist</Text>
              <Text style={styles.secondarySub}>Send an urgent message</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.secondaryAction}>
            <MessageSquare color={COLORS.crisis} size={24} />
            <View style={styles.actionDetails}>
              <Text style={styles.secondaryTitle}>Text an Emergency Contact</Text>
              <Text style={styles.secondarySub}>Reach out to your trusted circle</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Grounding Tip - Wellness touch */}
        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>Quick Grounding Tip</Text>
          <Text style={styles.tipText}>
            Try to find 5 things you can see, 4 things you can touch, and 3 things you can hear. Breathe slowly.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  closeButton: { padding: 20, alignSelf: 'flex-end' },
  content: { paddingHorizontal: 25, alignItems: 'center', paddingBottom: 40 },

  alertHeader: { alignItems: 'center', marginBottom: 40 },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.crisis,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    elevation: 5
  },
  title: { fontSize: 28, fontWeight: 'bold', color: COLORS.crisis, textAlign: 'center' },
  subtitle: { fontSize: 16, color: COLORS.text, opacity: 0.7, textAlign: 'center', marginTop: 10, lineHeight: 24 },

  primaryAction: {
    backgroundColor: COLORS.crisis,
    flexDirection: 'row',
    width: '100%',
    padding: 20,
    borderRadius: 24,
    alignItems: 'center',
    marginBottom: 30,
    elevation: 3
  },
  actionIcon: { marginRight: 20, backgroundColor: 'rgba(255,255,255,0.2)', padding: 10, borderRadius: 15 },
  actionTitle: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  actionSub: { color: 'white', opacity: 0.8, fontSize: 14 },

  section: { width: '100%', marginBottom: 30 },
  sectionTitle: { fontSize: 16, fontWeight: 'bold', color: COLORS.text, marginBottom: 15, opacity: 0.5 },

  secondaryAction: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    padding: 18,
    borderRadius: 20,
    alignItems: 'center',
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.crisis + '30'
  },
  actionDetails: { marginLeft: 15 },
  secondaryTitle: { fontSize: 16, fontWeight: '600', color: COLORS.text },
  secondarySub: { fontSize: 13, color: COLORS.text, opacity: 0.5 },

  tipCard: {
    backgroundColor: COLORS.primary + '10',
    padding: 20,
    borderRadius: 24,
    width: '100%',
    borderStyle: 'dashed',
    borderWidth: 1,
    borderColor: COLORS.primary
  },
  tipTitle: { fontSize: 16, fontWeight: 'bold', color: COLORS.primary, marginBottom: 5 },
  tipText: { fontSize: 14, color: COLORS.text, lineHeight: 20, opacity: 0.8 }
});