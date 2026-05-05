import { Stack } from 'expo-router';
import { COLORS } from '../src/constants/Theme';
import { AuthProvider } from '../src/context/AuthContext';


export default function RootLayout() {
  return (
    <AuthProvider>
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
      <Stack.Screen 
          name="screens/mood" 
          options={{ headerShown: false // This hides the "(tabs)" header entirely
          }} 
        />
      {/* Presentation: 'modal' makes the Crisis screen slide up from bottom */}
      <Stack.Screen name="screens/crisis" options={{ presentation: 'modal', headerShown: false  }} />

      <Stack.Screen name="screens/journal" options={{ title: 'New Entry', headerBackTitle: 'Back' , headerShown: false}} />
        <Stack.Screen name="screens/journal-history" options={{ title: 'My Journal', headerBackTitle: 'Back' , headerShown: false}} />

        <Stack.Screen name="screens/edit-profile" options={{ title: 'Edit Profile' , headerShown: false}} />
        <Stack.Screen name="screens/change-password" options={{ title: 'Security' , headerShown: false}} />
      
      <Stack.Screen name="screens/chat-history" options={{ title: 'Previous Chats' , headerShown: false}} />
      <Stack.Screen name="screens/chat-thread" options={{ title: 'Chat Details' , headerShown: false}} />

      <Stack.Screen
          name="screens/assessment"
          options={{ title: 'Assessment', headerBackTitle: 'Back' , headerShown: false}}
      />
    </Stack>
    </AuthProvider>
    
  );
}