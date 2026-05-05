// src/hooks/useCrisisGuard.js
// Call this hook in any screen that receives a risk_level from the backend.
// If risk_level === 'severe' or requires_crisis_intervention === true,
// it immediately navigates to the Crisis screen.
//
// Usage:
//   const { guard } = useCrisisGuard();
//   const result = await sendTextMessage(...);
//   guard(result.data);   // redirects if needed, otherwise no-op

import { useRouter } from 'expo-router';

export function useCrisisGuard() {
  const router = useRouter();

  const guard = (responseData) => {
    const isSevere =
      responseData?.risk_level === 'severe' ||
      responseData?.requires_crisis_intervention === true;

    if (isSevere) {
      // Replace so the user can't accidentally back out of crisis help
      router.replace('/screens/crisis');
      return true;
    }
    return false;
  };

  return { guard };
}