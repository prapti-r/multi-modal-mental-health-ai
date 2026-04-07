import React from 'react';
import { View, Text, StyleSheet, ScrollView, SafeAreaView, Dimensions } from 'react-native';
import { TrendingUp, Calendar, AlertTriangle, ArrowRight } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

const { width } = Dimensions.get('window');

export default function ReportsScreen() {
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Your Progress</Text>
          <Text style={styles.subtitle}>Insights from the last 7 days</Text>
        </View>

        {/* 1. Mood Trend Placeholder */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Mood History</Text>
            <TrendingUp color={COLORS.primary} size={20} />
          </View>
          <View style={styles.chartPlaceholder}>
             {/* Imagine a Sage Green Line Chart here */}
             <View style={styles.mockChartLine} />
             <View style={styles.chartLabels}>
                {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((d, i) => (
                  <Text key={i} style={styles.label}>{d}</Text>
                ))}
             </View>
          </View>
        </View>

        {/* 2. Stat Cards Row */}
        <View style={styles.row}>
          <View style={[styles.statCard, { backgroundColor: COLORS.secondary + '15' }]}>
            <Text style={styles.statLabel}>Avg. Mood</Text>
            <Text style={[styles.statValue, { color: COLORS.secondary }]}>Good</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: COLORS.primary + '15' }]}>
            <Text style={styles.statLabel}>Risk Level</Text>
            <Text style={[styles.statValue, { color: COLORS.primary }]}>Low</Text>
          </View>
        </View>

        {/* 3. Assessment Scores (PHQ-9 / GAD-7) */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Clinical Scores</Text>
            <Calendar color={COLORS.accent} size={20} />
          </View>

          <View style={styles.scoreRow}>
            <View>
              <Text style={styles.scoreName}>PHQ-9 (Depression)</Text>
              <Text style={styles.scoreDate}>Last taken: April 2</Text>
            </View>
            <Text style={styles.scoreNumber}>8/27</Text>
          </View>

          <View style={[styles.scoreRow, { borderBottomWidth: 0 }]}>
            <View>
              <Text style={styles.scoreName}>GAD-7 (Anxiety)</Text>
              <Text style={styles.scoreDate}>Last taken: March 28</Text>
            </View>
            <Text style={styles.scoreNumber}>5/21</Text>
          </View>
        </View>

        {/* 4. AI Insight Insight (Important for your Multimodal focus) */}
        <View style={styles.insightCard}>
          <View style={styles.insightIcon}>
            <AlertTriangle color={COLORS.primary} size={24} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.insightTitle}>AI Sentiment Insight</Text>
            <Text style={styles.insightText}>
              Your vocal tone in recent check-ins shows 15% more stability than last week. Keep it up!
            </Text>
          </View>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContent: { padding: 25 },
  header: { marginBottom: 30 },
  title: { fontSize: 28, fontWeight: 'bold', color: COLORS.text },
  subtitle: { fontSize: 16, color: COLORS.text, opacity: 0.5 },

  section: {
    backgroundColor: COLORS.card,
    borderRadius: 24,
    padding: 20,
    marginBottom: 20,
    elevation: 2
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20
  },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text },

  chartPlaceholder: { height: 120, justifyContent: 'flex-end' },
  mockChartLine: {
    height: 60,
    width: '100%',
    borderBottomWidth: 2,
    borderColor: COLORS.primary,
    borderLeftWidth: 0,
    backgroundColor: COLORS.primary + '10'
  },
  chartLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 10 },
  label: { fontSize: 12, color: COLORS.text, opacity: 0.4 },

  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  statCard: { width: '47%', padding: 20, borderRadius: 20, alignItems: 'center' },
  statLabel: { fontSize: 14, color: COLORS.text, opacity: 0.6, marginBottom: 5 },
  statValue: { fontSize: 20, fontWeight: 'bold' },

  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.gray
  },
  scoreName: { fontSize: 16, fontWeight: '500', color: COLORS.text },
  scoreDate: { fontSize: 12, color: COLORS.text, opacity: 0.4 },
  scoreNumber: { fontSize: 18, fontWeight: 'bold', color: COLORS.text },

  insightCard: {
    backgroundColor: COLORS.card,
    flexDirection: 'row',
    padding: 20,
    borderRadius: 24,
    borderLeftWidth: 5,
    borderLeftColor: COLORS.primary,
    alignItems: 'center',
    marginBottom: 30
  },
  insightIcon: { marginRight: 15 },
  insightTitle: { fontSize: 16, fontWeight: 'bold', color: COLORS.text },
  insightText: { fontSize: 14, color: COLORS.text, opacity: 0.7, marginTop: 4 }
});