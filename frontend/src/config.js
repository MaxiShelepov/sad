import Constants from 'expo-constants';

const rawBackendUrl =
  process.env.EXPO_PUBLIC_BACKEND_URL || Constants.expoConfig?.extra?.backendUrl || '';

const normalizedBackendUrl = rawBackendUrl.replace(/\/$/, '');

export const BACKEND_URL = normalizedBackendUrl;
export const API_BASE_URL = `${normalizedBackendUrl}/api`;
export const APP_NAME = 'WLESS PRO Mobile';
