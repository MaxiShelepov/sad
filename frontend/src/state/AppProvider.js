import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { api } from '../api';

const HWID_STORAGE_KEY = 'wless-pro-mobile-hwid';
const AppContext = createContext(null);

function createHwid() {
  const stamp = Date.now().toString(36).toUpperCase();
  const random = Math.random().toString(36).slice(2, 10).toUpperCase();
  return `ANDROID-${stamp}-${random}`;
}

export function AppProvider({ children }) {
  const [hwid, setHwid] = useState('');
  const [subscription, setSubscription] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const refreshAll = useCallback(async (targetHwid, silent = false) => {
    if (!targetHwid) {
      return;
    }

    if (!silent) {
      setRefreshing(true);
    }

    try {
      const [licenseData, dashboardData] = await Promise.all([
        api.checkLicense(targetHwid),
        api.getDashboard(targetHwid),
      ]);
      setSubscription(licenseData.subscription);
      setDashboard(dashboardData);
      setError('');
    } catch (requestError) {
      setError(requestError.message || 'Не удалось обновить данные приложения');
    } finally {
      if (!silent) {
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      try {
        let storedHwid = await AsyncStorage.getItem(HWID_STORAGE_KEY);
        if (!storedHwid) {
          storedHwid = createHwid();
          await AsyncStorage.setItem(HWID_STORAGE_KEY, storedHwid);
        }

        if (!mounted) {
          return;
        }

        setHwid(storedHwid);
        await refreshAll(storedHwid, true);
      } catch (bootstrapError) {
        if (mounted) {
          setError(bootstrapError.message || 'Ошибка инициализации приложения');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      mounted = false;
    };
  }, [refreshAll]);

  const value = useMemo(
    () => ({
      hwid,
      subscription,
      dashboard,
      loading,
      refreshing,
      error,
      refreshAll: (targetHwid = hwid, silent = false) => refreshAll(targetHwid, silent),
      setSubscription,
      setDashboard,
    }),
    [dashboard, error, hwid, loading, refreshAll, refreshing, subscription],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppState must be used inside AppProvider');
  }
  return context;
}
