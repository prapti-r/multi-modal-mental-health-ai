import { Stack } from 'expo-router';
import { COLORS } from '../src/constants/Theme';

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: COLORS.background },
        headerTintColor: COLORS.text,
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      {/* Hide header for Welcome and Auth */}
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="auth/login" options={{ title: 'Sign In' }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      {/* Presentation: 'modal' makes the Crisis screen slide up from bottom */}
      <Stack.Screen name="screens/crisis" options={{ presentation: 'modal', title: 'Emergency Help' }} />
    </Stack>
  );
}