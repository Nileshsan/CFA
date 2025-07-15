import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  Dimensions,
  StatusBar
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { Chart } from '../components/Chart';

const { width } = Dimensions.get('window');

interface AnalyticsCard {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  icon: string;
  color: string;
}

export default function AnalyticsScreen() {
  const [selectedPeriod, setSelectedPeriod] = useState('month');

  const analyticsData: AnalyticsCard[] = [
    {
      title: 'Cash Flow Trend',
      value: '+15.2%',
      change: 'vs last month',
      isPositive: true,
      icon: 'trending-up',
      color: '#4caf50'
    },
    {
      title: 'Revenue Growth',
      value: '+8.7%',
      change: 'vs last month',
      isPositive: true,
      icon: 'bar-chart',
      color: '#2196f3'
    },
    {
      title: 'Expense Ratio',
      value: '23.4%',
      change: 'vs last month',
      isPositive: false,
      icon: 'pie-chart',
      color: '#ff9800'
    },
    {
      title: 'Profit Margin',
      value: '31.2%',
      change: 'vs last month',
      isPositive: true,
      icon: 'analytics',
      color: '#9c27b0'
    }
  ];

  const renderAnalyticsCard = (card: AnalyticsCard, index: number) => (
    <View key={index} style={styles.analyticsCard}>
      <LinearGradient
        colors={[card.color + '20', card.color + '10']}
        style={styles.cardGradient}
      >
        <View style={styles.cardHeader}>
          <Ionicons name={card.icon as any} size={24} color={card.color} />
          <View style={[styles.changeBadge, { backgroundColor: card.isPositive ? '#4caf50' : '#f44336' }]}>
            <Ionicons 
              name={card.isPositive ? 'arrow-up' : 'arrow-down'} 
              size={12} 
              color="#fff" 
            />
            <Text style={styles.changeText}>{card.change}</Text>
          </View>
        </View>
        <Text style={styles.cardValue}>{card.value}</Text>
        <Text style={styles.cardTitle}>{card.title}</Text>
      </LinearGradient>
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar backgroundColor="#2e7d32" barStyle="light-content" />
      
      {/* Header */}
      <LinearGradient
        colors={['#2e7d32', '#388e3c']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>Analytics</Text>
            <Text style={styles.headerSubtitle}>Advanced insights & trends</Text>
          </View>
          <TouchableOpacity style={styles.headerButton}>
            <Ionicons name="settings" size={24} color="#fff" />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Period Selector */}
        <View style={styles.periodSelector}>
          {['week', 'month', 'quarter', 'year'].map((period) => (
            <TouchableOpacity
              key={period}
              style={[
                styles.periodButton,
                selectedPeriod === period && styles.periodButtonActive
              ]}
              onPress={() => setSelectedPeriod(period)}
            >
              <Text style={[
                styles.periodText,
                selectedPeriod === period && styles.periodTextActive
              ]}>
                {period.charAt(0).toUpperCase() + period.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Analytics Cards */}
        <View style={styles.analyticsGrid}>
          {analyticsData.map((card, index) => renderAnalyticsCard(card, index))}
        </View>

        {/* Chart Section */}
        <View style={styles.chartSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Performance Overview</Text>
            <TouchableOpacity>
              <Ionicons name="ellipsis-horizontal" size={20} color="#666" />
            </TouchableOpacity>
          </View>
          <View style={styles.chartContainer}>
            <Chart />
          </View>
        </View>

        {/* Insights Section */}
        <View style={styles.insightsSection}>
          <Text style={styles.sectionTitle}>AI Insights</Text>
          
          <View style={styles.insightCard}>
            <View style={styles.insightIcon}>
              <Ionicons name="bulb" size={24} color="#4caf50" />
            </View>
            <View style={styles.insightContent}>
              <Text style={styles.insightTitle}>Revenue Optimization</Text>
              <Text style={styles.insightText}>
                Your revenue has increased by 15.2% this month. Consider expanding your most profitable services.
              </Text>
            </View>
          </View>

          <View style={styles.insightCard}>
            <View style={styles.insightIcon}>
              <Ionicons name="warning" size={24} color="#ff9800" />
            </View>
            <View style={styles.insightContent}>
              <Text style={styles.insightTitle}>Expense Alert</Text>
              <Text style={styles.insightText}>
                Operating expenses are 8% higher than average. Review non-essential costs.
              </Text>
            </View>
          </View>

          <View style={styles.insightCard}>
            <View style={styles.insightIcon}>
              <Ionicons name="trending-up" size={24} color="#2196f3" />
            </View>
            <View style={styles.insightContent}>
              <Text style={styles.insightTitle}>Growth Opportunity</Text>
              <Text style={styles.insightText}>
                Market conditions are favorable for expansion. Consider new investments.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fff8',
  },
  header: {
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  periodSelector: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginVertical: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: '#2e7d32',
  },
  periodText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '500',
  },
  periodTextActive: {
    color: '#fff',
  },
  analyticsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    marginBottom: 20,
  },
  analyticsCard: {
    width: (width - 60) / 2,
    marginBottom: 16,
    marginHorizontal: 4,
  },
  cardGradient: {
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  changeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  changeText: {
    fontSize: 10,
    color: '#fff',
    marginLeft: 2,
    fontWeight: 'bold',
  },
  cardValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  cardTitle: {
    fontSize: 12,
    color: '#666',
  },
  chartSection: {
    marginHorizontal: 20,
    marginBottom: 20,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  chartContainer: {
    height: 200,
  },
  insightsSection: {
    marginHorizontal: 20,
    marginBottom: 20,
  },
  insightCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  insightIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  insightContent: {
    flex: 1,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  insightText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
}); 