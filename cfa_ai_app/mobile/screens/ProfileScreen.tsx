import React, { useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity, 
  Switch,
  Alert,
  Image
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

interface SettingItem {
  title: string;
  subtitle?: string;
  icon: string;
  type: 'toggle' | 'navigate' | 'action';
  value?: boolean;
  onPress?: () => void;
  onToggle?: (value: boolean) => void;
}

export default function ProfileScreen() {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [biometric, setBiometric] = useState(true);

  const settings: SettingItem[] = [
    {
      title: 'Notifications',
      subtitle: 'Receive push notifications',
      icon: 'notifications',
      type: 'toggle',
      value: notifications,
      onToggle: setNotifications
    },
    {
      title: 'Dark Mode',
      subtitle: 'Use dark theme',
      icon: 'moon',
      type: 'toggle',
      value: darkMode,
      onToggle: setDarkMode
    },
    {
      title: 'Biometric Login',
      subtitle: 'Use fingerprint or face ID',
      icon: 'finger-print',
      type: 'toggle',
      value: biometric,
      onToggle: setBiometric
    },
    {
      title: 'Account Settings',
      subtitle: 'Manage your account',
      icon: 'person',
      type: 'navigate',
      onPress: () => Alert.alert('Account Settings', 'Navigate to account settings')
    },
    {
      title: 'Privacy & Security',
      subtitle: 'Manage privacy settings',
      icon: 'shield-checkmark',
      type: 'navigate',
      onPress: () => Alert.alert('Privacy', 'Navigate to privacy settings')
    },
    {
      title: 'Help & Support',
      subtitle: 'Get help and contact support',
      icon: 'help-circle',
      type: 'navigate',
      onPress: () => Alert.alert('Support', 'Navigate to help & support')
    },
    {
      title: 'About CFA AI',
      subtitle: 'Version 1.0.0',
      icon: 'information-circle',
      type: 'navigate',
      onPress: () => Alert.alert('About', 'CFA AI - Smart Cash Flow Analytics\nVersion 1.0.0')
    },
    {
      title: 'Logout',
      subtitle: 'Sign out of your account',
      icon: 'log-out',
      type: 'action',
      onPress: () => {
        Alert.alert(
          'Logout',
          'Are you sure you want to logout?',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Logout', style: 'destructive', onPress: () => Alert.alert('Logged out') }
          ]
        );
      }
    }
  ];

  const renderSettingItem = (item: SettingItem, index: number) => (
    <TouchableOpacity
      key={index}
      style={styles.settingItem}
      onPress={item.onPress}
      disabled={item.type === 'toggle'}
    >
      <View style={styles.settingLeft}>
        <View style={[styles.iconContainer, { backgroundColor: getIconColor(item.icon) + '20' }]}>
          <Ionicons name={item.icon as any} size={20} color={getIconColor(item.icon)} />
        </View>
        <View style={styles.settingText}>
          <Text style={styles.settingTitle}>{item.title}</Text>
          {item.subtitle && <Text style={styles.settingSubtitle}>{item.subtitle}</Text>}
        </View>
      </View>
      
      {item.type === 'toggle' ? (
        <Switch
          value={item.value}
          onValueChange={item.onToggle}
          trackColor={{ false: '#e0e0e0', true: '#4caf50' }}
          thumbColor={item.value ? '#fff' : '#f4f3f4'}
        />
      ) : (
        <Ionicons name="chevron-forward" size={20} color="#ccc" />
      )}
    </TouchableOpacity>
  );

  const getIconColor = (icon: string): string => {
    const colors: { [key: string]: string } = {
      'notifications': '#2196f3',
      'moon': '#9c27b0',
      'finger-print': '#4caf50',
      'person': '#ff9800',
      'shield-checkmark': '#f44336',
      'help-circle': '#00bcd4',
      'information-circle': '#607d8b',
      'log-out': '#f44336'
    };
    return colors[icon] || '#666';
  };

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={['#2e7d32', '#388e3c']}
        style={styles.header}
      >
        <View style={styles.profileSection}>
          <View style={styles.avatarContainer}>
            <LinearGradient
              colors={['#4caf50', '#2e7d32']}
              style={styles.avatar}
            >
              <Ionicons name="person" size={40} color="#fff" />
            </LinearGradient>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>John Doe</Text>
            <Text style={styles.profileEmail}>john.doe@example.com</Text>
            <Text style={styles.profileRole}>CFA AI User</Text>
          </View>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Settings</Text>
          <View style={styles.settingsContainer}>
            {settings.map((item, index) => renderSettingItem(item, index))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>App Statistics</Text>
          <View style={styles.statsContainer}>
            <View style={styles.statCard}>
              <Ionicons name="analytics" size={24} color="#4caf50" />
              <Text style={styles.statValue}>156</Text>
              <Text style={styles.statLabel}>Transactions</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="trending-up" size={24} color="#2196f3" />
              <Text style={styles.statValue}>₹2.4M</Text>
              <Text style={styles.statLabel}>Total Revenue</Text>
            </View>
            <View style={styles.statCard}>
              <Ionicons name="calendar" size={24} color="#ff9800" />
              <Text style={styles.statValue}>45</Text>
              <Text style={styles.statLabel}>Days Active</Text>
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
    paddingBottom: 30,
    paddingHorizontal: 20,
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    marginRight: 20,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    marginBottom: 4,
  },
  profileRole: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
  },
  content: {
    flex: 1,
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginHorizontal: 20,
    marginBottom: 16,
  },
  settingsContainer: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  settingText: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  statsContainer: {
    flexDirection: 'row',
    marginHorizontal: 20,
    justifyContent: 'space-between',
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginHorizontal: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
}); 