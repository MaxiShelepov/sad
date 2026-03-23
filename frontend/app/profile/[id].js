import { router, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '../../src/api';
import { ActionButton } from '../../src/components/ActionButton';
import { LogTerminal } from '../../src/components/LogTerminal';
import { Screen } from '../../src/components/Screen';
import { StatCard } from '../../src/components/StatCard';
import { StatusPill } from '../../src/components/StatusPill';
import { useAppState } from '../../src/state/AppProvider';
import { getTheme, radii, spacing } from '../../src/theme';

const MODES = [
  { key: 'calm', label: 'Спокойный' },
  { key: 'balanced', label: 'Баланс' },
  { key: 'turbo', label: 'Турбо' },
];

export default function ProfileDetailsScreen() {
  const theme = getTheme();
  const { id } = useLocalSearchParams();
  const { hwid } = useAppState();
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [mode, setMode] = useState('balanced');
  const [minutes, setMinutes] = useState('15');
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');

  const activeJob = useMemo(() => jobs.find((job) => job.status === 'running' || job.status === 'pending') || jobs[0], [jobs]);

  const loadData = useCallback(async () => {
    if (!id) {
      return;
    }

    try {
      setLoading(true);
      const profileData = await api.getProfile(id);
      const warmupsData = await api.getWarmups(profileData.hwid || hwid);
      setProfile(profileData);
      setJobs(warmupsData.filter((item) => item.profile_id === id));
      setError('');
    } catch (requestError) {
      setError(requestError.message || 'Не удалось загрузить профиль');
    } finally {
      setLoading(false);
    }
  }, [hwid, id]);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData]),
  );

  useEffect(() => {
    if (!activeJob || !['pending', 'running'].includes(activeJob.status)) {
      return undefined;
    }

    const interval = setInterval(() => {
      loadData();
    }, 4000);
    return () => clearInterval(interval);
  }, [activeJob, loadData]);

  async function startWarmup() {
    const targetHwid = profile?.hwid || hwid;
    try {
      setPending(true);
      await api.startWarmup({ hwid: targetHwid, profile_id: id, mode, minutes: Number(minutes) || 15 });
      await loadData();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось запустить прогрев');
    } finally {
      setPending(false);
    }
  }

  async function stopWarmup() {
    if (!activeJob) {
      return;
    }

    try {
      setPending(true);
      await api.stopWarmup(activeJob.id);
      await loadData();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось остановить прогрев');
    } finally {
      setPending(false);
    }
  }

  if (loading) {
    return (
      <Screen testID="profile-loading-screen">
        <View style={styles.centered}>
          <ActivityIndicator color={theme.primary} size="large" />
        </View>
      </Screen>
    );
  }

  if (!profile) {
    return (
      <Screen testID="profile-not-found-screen">
        <ActionButton icon="arrow-left" label="Назад" onPress={() => router.back()} testID="profile-back-button-empty" />
        <Text style={[styles.error, { color: theme.danger }]}>Профиль не найден</Text>
      </Screen>
    );
  }

  return (
    <Screen testID="profile-details-screen">
      <ActionButton compact icon="arrow-left" label="Назад" onPress={() => router.back()} testID="profile-back-button" variant="secondary" />

      <View style={[styles.profileCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.rowBetween}>
          <View style={styles.flexItem}>
            <Text style={[styles.title, { color: theme.textPrimary }]}>{profile.name}</Text>
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>{profile.email}</Text>
          </View>
          <StatusPill
            label={activeJob?.status ? activeJob.status.toUpperCase() : 'IDLE'}
            tone={activeJob?.status === 'running' ? 'success' : activeJob?.status === 'error' ? 'danger' : 'neutral'}
            testID="profile-status-pill"
          />
        </View>

        <Text style={[styles.meta, { color: theme.textSecondary }]}>
          {profile.proxy || 'Без прокси'} · {profile.fingerprint.browser} · {profile.fingerprint.os_name}
        </Text>

        <View style={styles.statsRow}>
          <StatCard label="Trust" value={profile.stats.trust_score} accent="primary" testID="profile-trust-card" />
          <StatCard label="Операций" value={profile.stats.total_operations} accent="success" testID="profile-operations-card" />
        </View>
      </View>

      <View style={[styles.profileCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionTitle, { color: theme.textPrimary }]}>Режим прогрева</Text>
        <View style={styles.modeRow}>
          {MODES.map((item) => (
            <View key={item.key} style={styles.modeItem}>
              <ActionButton
                compact
                icon="cpu"
                label={item.label}
                onPress={() => setMode(item.key)}
                testID={`mode-${item.key}-button`}
                variant={mode === item.key ? 'primary' : 'secondary'}
              />
            </View>
          ))}
        </View>

        <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Длительность, минут</Text>
        <TextInput
          keyboardType="number-pad"
          onChangeText={setMinutes}
          style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
          testID="warmup-minutes-input"
          value={minutes}
        />

        <View style={styles.actionRow}>
          <View style={styles.actionItem}>
            <ActionButton icon="play" label="Старт" onPress={startWarmup} disabled={pending} testID="start-warmup-button" />
          </View>
          <View style={styles.actionItem}>
            <ActionButton icon="square" label="Стоп" onPress={stopWarmup} disabled={!activeJob || pending} testID="stop-warmup-button" variant="danger" />
          </View>
        </View>
      </View>

      <View style={[styles.profileCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.rowBetween}>
          <View style={styles.flexItem}>
            <Text style={[styles.sectionTitle, { color: theme.textPrimary }]}>Отпечаток браузера</Text>
            <Text style={[styles.meta, { color: theme.textSecondary }]}>
              {profile.fingerprint.browser} {profile.fingerprint.browser_version} · {profile.fingerprint.screen_width}x{profile.fingerprint.screen_height}
            </Text>
            <Text style={[styles.meta, { color: theme.textSecondary }]}>
              {profile.fingerprint.timezone} · {profile.fingerprint.webgl_vendor_group}
            </Text>
          </View>
          <ActionButton
            compact
            icon="sliders"
            label="Изменить"
            onPress={() => router.push(`/profile/${id}/fingerprint`)}
            testID="edit-fingerprint-button"
            variant="secondary"
          />
        </View>
      </View>

      {activeJob ? (
        <View style={styles.statsRow}>
          <StatCard label="OPM" value={activeJob.metrics.opm} accent="warning" testID="warmup-opm-card" />
          <StatCard label="Прогресс" value={`${Math.round((activeJob.metrics.progress || 0) * 100)}%`} accent="primary" testID="warmup-progress-card" />
        </View>
      ) : null}

      {error ? <Text style={[styles.error, { color: theme.danger }]}>{error}</Text> : null}
      <LogTerminal logs={activeJob?.logs || []} testID="profile-log-terminal" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  centered: {
    paddingTop: spacing.xl,
    alignItems: 'center',
  },
  profileCard: {
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.md,
    gap: spacing.md,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: spacing.md,
  },
  flexItem: {
    flex: 1,
    gap: 4,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 16,
  },
  meta: {
    fontSize: 14,
    lineHeight: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  modeRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  modeItem: {
    flex: 1,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
  },
  actionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionItem: {
    flex: 1,
  },
  error: {
    fontSize: 14,
    fontWeight: '600',
  },
});
