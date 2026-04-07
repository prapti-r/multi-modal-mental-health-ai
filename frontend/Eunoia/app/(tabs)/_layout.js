import { Tabs } from 'expo-router';
import { Home, MessageCircle, BarChart2, User } from 'lucide-react-native';
import { COLORS } from '../../src/constants/Theme';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        // Using your warm cream background for the tab bar
        tabBarStyle: {
          backgroundColor: '#FDFCF0',
          borderTopWidth: 0,
          height: 90,
          paddingBottom: 30,
          paddingTop: 10,
          elevation: 10, // Shadow for Android
          shadowColor: '#000', // Shadow for iOS
          shadowOpacity: 0.05,
          shadowRadius: 10,
        },
        tabBarActiveTintColor: '#9DBF9E', // Sage Green for active tab
        tabBarInactiveTintColor: '#999',
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Today',
          tabBarIcon: ({ color }) => <Home color={color} size={24} />,
        }}
      />
      <Tabs.Screen
        name="chatbot"
        options={{
          title: 'AI Chat',
          tabBarIcon: ({ color }) => <MessageCircle color={color} size={24} />,
        }}
      />
      <Tabs.Screen
        name="reports"
        options={{
          title: 'Insights',
          tabBarIcon: ({ color }) => <BarChart2 color={color} size={24} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <User color={color} size={24} />,
        }}
      />
    </Tabs>
  );
}