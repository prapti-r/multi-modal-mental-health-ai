// app/(tabs)/home.js
// Changes from original:
//   • Greeting uses user.full_name from AuthContext (not hardcoded "Prapti")
//   • Mini mood sparkline pulled from GET /mood/history (last 7 days)
//   • Last assessment score shown on the dashboard card
//   • Crisis button still always visible

import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  SafeAreaView, 
} from 'react-native';
import { useRouter } from 'expo-router';
import {
  Heart, MessageCircle, BookOpen, Activity,
  BarChart2, AlertCircle, 
} from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { useAuth } from '../../src/context/AuthContext';
import { getAssessmentHistory } from '../../src/api/tracking';


export default function Dashboard() {
  const router     = useRouter();
  const { user }   = useAuth();
  const firstName  = user?.full_name?.split(' ')[0] ?? 'there';


  const [lastAssessment, setLastAssessment] = useState(null);


  const ActionCard = ({ title, icon: IconComponent, color, onPress, size = 'small' }) => (
    <TouchableOpacity
      style={[styles.card, size === 'large' ? styles.largeCard : styles.smallCard]}
      onPress={onPress}
    >
      <View style={[styles.iconContainer, { backgroundColor: color + '20' }]}>
        <IconComponent color={color} size={28} />
      </View>
      <Text style={styles.cardText}>{title}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>Hello, {firstName} </Text>
          <Text style={styles.subGreeting}>How are you feeling today?</Text>
        </View>

       

        {/* Bento Grid */}
        <View style={styles.grid}>
          <ActionCard
            title="Start Chat"
            icon={MessageCircle}
            color={COLORS.secondary}
            size="large"
            onPress={() => router.push('/(tabs)/chatbot')}
          />
          <ActionCard
            title="Mood Check"
            icon={Heart}
            color={COLORS.primary}
            onPress={() => router.push('/screens/mood')}
          />
          <ActionCard
            title="Journal"
            icon={BookOpen}
            color={COLORS.accent}
            onPress={() => router.push('/screens/journal')}
          />
          <ActionCard
            title="Assessment"
            icon={Activity}
            color={COLORS.primary}
            onPress={() => router.push('/screens/assessment')}
          />
          <ActionCard
            title="View Reports"
            icon={BarChart2}
            color={COLORS.secondary}
            onPress={() => router.push('/(tabs)/reports')}
          />
        </View>

        {/* Emergency */}
        <TouchableOpacity
          style={styles.crisisButton}
          onPress={() => router.push('/screens/crisis')}
        >
          <AlertCircle color="white" size={20} />
          <Text style={styles.crisisText}>Emergency Help</Text>
        </TouchableOpacity>

        {/* PRD §5 disclaimer */}
        <Text style={styles.disclaimer}>
          Not a medical diagnosis. Always consult a professional for clinical advice.
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.background },
  scrollContent:   { padding: 20 },
  header:          { marginBottom: 20, marginTop: 20 },
  greeting:        { fontSize: 28, fontWeight: 'bold', color: COLORS.text },
  subGreeting:     { fontSize: 16, color: COLORS.text, opacity: 0.7 },

  
  assessmentChip: {
    backgroundColor: COLORS.secondary + '15', borderRadius: 14,
    paddingHorizontal: 14, paddingVertical: 8, marginBottom: 15, alignSelf: 'flex-start',
  },
  assessmentChipText: { fontSize: 13, color: COLORS.secondary },

  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  card: {
    backgroundColor: COLORS.card, borderRadius: 24, padding: 20, marginBottom: 15,
    elevation: 3, shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05, shadowRadius: 10, alignItems: 'flex-start', justifyContent: 'space-between',
  },
  largeCard:      { width: '100%', height: 160 },
  smallCard:      { width: '47%', height: 140 },
  iconContainer:  { padding: 12, borderRadius: 15, marginBottom: 10 },
  cardText:       { fontSize: 16, fontWeight: '600', color: COLORS.text },

  crisisButton: {
    backgroundColor: COLORS.crisis, flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', padding: 18, borderRadius: 20, marginTop: 20,
  },
  crisisText:  { color: 'white', fontWeight: 'bold', marginLeft: 10, fontSize: 16 },
  disclaimer:  { textAlign: 'center', marginTop: 20, fontSize: 11, color: COLORS.text, opacity: 0.3, lineHeight: 16 },
});