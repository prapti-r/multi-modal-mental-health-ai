// app/(tabs)/reports.js

import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, SafeAreaView,
  ActivityIndicator, TouchableOpacity, Alert, Dimensions,
} from 'react-native';
import { useRouter } from 'expo-router';
import { TrendingUp, Calendar, AlertTriangle, RefreshCw, Activity } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';
import { getWeeklyReport } from '../../src/api/reports';
import { getAssessmentHistory, getMoodHistory } from '../../src/api/tracking';

const { width } = Dimensions.get('window');
// Padding adjustment to match the card style
const CHART_MARGIN = 40;
const GRAPH_WIDTH = width - (CHART_MARGIN * 2);
const GRAPH_HEIGHT = 80;

export default function ReportsScreen() {
  const router = useRouter();
  const [report, setReport] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [moodPoints, setMoodPoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [reportRes, assessRes, moodRes] = await Promise.all([
        getWeeklyReport(),
        getAssessmentHistory(1, 10),
        getMoodHistory(1, 7),
      ]);
      setReport(reportRes.data);
      setAssessments(assessRes.data.entries ?? []);
      
      // Ensure we have 7 days of data for the UI mapping
      setMoodPoints(moodRes.data.data_points ?? []);
    } catch (err) {
      Alert.alert('Error', 'Could not load your report.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleRefresh = () => { setRefreshing(true); fetchData(); };

  const renderMoodGraph = () => {
    const days = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    // Map scores to the last 7 days; default to mid-range if no data
    const scores = moodPoints.map(p => p.mood_score).slice(-7);
    
    // Fill remaining days if less than 7 points
    while (scores.length < 7) scores.unshift(null);

    const stepX = GRAPH_WIDTH / 6;

    return (
      <View style={styles.graphContainer}>
        <View style={styles.svgPlaceholder}>
          {scores.map((score, i) => {
            if (score === null) return null;
            
            const x = i * stepX;
            // Normalize score (assuming 1-10 range)
            const y = GRAPH_HEIGHT - ((score / 10) * GRAPH_HEIGHT);

            return (
              <React.Fragment key={i}>
                {/* Connecting Line */}
                {i < scores.length - 1 && scores[i+1] !== null && (
                  <View style={[
                    styles.line,
                    {
                      left: x,
                      top: y,
                      width: stepX + 2,
                      transform: [
                        { rotate: `${Math.atan2( (GRAPH_HEIGHT - ((scores[i+1] / 10) * GRAPH_HEIGHT)) - y, stepX) * (180 / Math.PI)}deg` }
                      ],
                      transformOrigin: 'left top'
                    }
                  ]} />
                )}
                {/* Data Dot */}
                <View style={[styles.dot, { left: x - 4, top: y - 4 }]} />
              </React.Fragment>
            );
          })}
        </View>
        
        {/* Day Labels */}
        <View style={styles.dayLabelsRow}>
          {days.map((day, index) => (
            <Text key={index} style={styles.dayLabel}>{day}</Text>
          ))}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      </SafeAreaView>
    );
  }

  const label = report?.report?.prediction_label ?? 'Stable';
  const narrative = report?.report?.qualitative_report ?? '';
  const isCrisis = report?.requires_crisis_intervention ?? false;

  const lastPhq = assessments.find((a) => a.test_type === 'PHQ-9');
  const lastGad = assessments.find((a) => a.test_type === 'GAD-7');

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Your Progress</Text>
            <Text style={styles.subtitle}>Insights from the last 7 days</Text>
          </View>
          <TouchableOpacity onPress={handleRefresh}>
            <RefreshCw color={COLORS.primary} size={20} />
          </TouchableOpacity>
        </View>

        {isCrisis && (
          <TouchableOpacity style={styles.crisisBanner} onPress={() => router.push('/screens/crisis')}>
            <AlertTriangle color="white" size={18} />
            <Text style={styles.crisisBannerText}>Immediate help available</Text>
          </TouchableOpacity>
        )}

        {/* Mood History Card */}
        <View style={styles.mainCard}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Mood History</Text>
            <TrendingUp color={COLORS.primary} size={20} />
          </View>
          {renderMoodGraph()}
        </View>


        {/* Clinical Scores */}
        <View style={styles.mainCard}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Clinical Scores</Text>
            <Calendar color={COLORS.accent} size={20} />
          </View>
          <ScoreRow
            name="PHQ-9 (Depression)"
            score={lastPhq?.total_score}
            max={27}
            date={lastPhq?.created_at}
          />
          <ScoreRow
            name="GAD-7 (Anxiety)"
            score={lastGad?.total_score}
            max={21}
            date={lastGad?.created_at}
            last
          />
        </View>

        {/* AI Insight */}
        {!!narrative && (
          <View style={styles.insightCard}>
            <View style={styles.insightHeader}>
               <Activity color={COLORS.primary} size={20} />
               <Text style={styles.insightTitle}>AI Sentiment Insight</Text>
            </View>
            <Text style={styles.insightText}>{narrative}</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function ScoreRow({ name, score, max, date, last }) {
  const dateStr = date ? new Date(date).toLocaleDateString('en-US', { month: 'long', day: 'numeric' }) : 'Pending';
  return (
    <View style={[styles.scoreRow, last && { borderBottomWidth: 0 }]}>
      <View>
        <Text style={styles.scoreName}>{name}</Text>
        <Text style={styles.scoreDate}>Last taken: {dateStr}</Text>
      </View>
      <Text style={styles.scoreNumber}>{score != null ? `${score}/${max}` : '—'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9F9F7' }, // Off-white background like image
  scrollContent: { padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 25 },
  title: { fontSize: 26, fontWeight: '700', color: '#333' },
  subtitle: { fontSize: 15, color: '#999', marginTop: 4 },
  
  mainCard: { 
    backgroundColor: '#FFF', borderRadius: 24, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOpacity: 0.03, shadowRadius: 10, elevation: 2 
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  cardTitle: { fontSize: 17, fontWeight: '600', color: '#333' },

  // Graph Styles
  graphContainer: { marginTop: 10 },
  svgPlaceholder: { height: GRAPH_HEIGHT, width: GRAPH_WIDTH, marginBottom: 15 },
  line: { position: 'absolute', height: 2, backgroundColor: '#88B04B', opacity: 0.5 },
  dot: { position: 'absolute', width: 8, height: 8, borderRadius: 4, backgroundColor: '#88B04B' },
  dayLabelsRow: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: '#EEE', paddingTop: 10 },
  dayLabel: { fontSize: 12, color: '#BBB', width: 20, textAlign: 'center' },

  // Stats Row
  statsRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 16 },
  statBox: { 
    backgroundColor: '#F3F5F7', width: '48%', borderRadius: 20, padding: 20, alignItems: 'center' 
  },
  statLabel: { fontSize: 13, color: '#999', marginBottom: 6 },
  statValue: { fontSize: 18, fontWeight: '700' },

  // Clinical Scores
  scoreRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 15, borderBottomWidth: 1, borderBottomColor: '#F0F0F0' },
  scoreName: { fontSize: 15, fontWeight: '600', color: '#333' },
  scoreDate: { fontSize: 12, color: '#AAA', marginTop: 4 },
  scoreNumber: { fontSize: 16, fontWeight: '700', color: '#333' },

  // Insight
  insightCard: { backgroundColor: '#FFF', borderRadius: 24, padding: 20, borderLeftWidth: 4, borderLeftColor: '#88B04B' },
  insightHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  insightTitle: { fontSize: 16, fontWeight: '700', color: '#333' },
  insightText: { fontSize: 14, color: '#666', lineHeight: 20 },

  crisisBanner: { backgroundColor: COLORS.crisis, padding: 12, borderRadius: 12, flexDirection: 'row', gap: 8, marginBottom: 16 },
  crisisBannerText: { color: '#FFF', fontWeight: '600' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' }
});