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