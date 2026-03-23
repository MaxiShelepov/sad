import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from '../../src/api';
import { ActionButton } from '../../src/components/ActionButton';
import { LogTerminal } from '../../src/components/LogTerminal';
import { Screen } from '../../src/components/Screen';
import { StatusPill } from '../../src/components/StatusPill';
import { useAppState } from '../../src/state/AppProvider';
import { getTheme, radii, spacing } from '../../src/theme';

const MODES = ['calm', 'balanced', 'turbo'];

export default function FarmScreen() {
  const theme = getTheme();
  const { hwid } = useAppState();
  const [profiles, setProfiles] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selected, setSelected] = useState({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const selectedItems = useMemo(
    () =>
      Object.entries(selected)
        .filter(([, value]) => value?.checked)
        .map(([profileId, value]) => ({ profile_id: profileId, mode: value.mode || 'balanced', minutes: value.minutes || 15 })),
    [selected],
  );

  const loadData = useCallback(async () => {
    if (!hwid) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const [profilesData, jobsData] = await Promise.all([api.getProfiles(hwid), api.getWarmups(hwid)]);
      setProfiles(profilesData);
      setJobs(jobsData.filter((item) => item.group_id || ['pending', 'running'].includes(item.status)));
      setError('');
    } catch (requestError) {
      setError(requestError.message || 'Не удалось загрузить ферму');
    } finally {
      setLoading(false);
    }
  }, [hwid]);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData]),
  );

  useEffect(() => {
    if (hwid) {
      loadData();
    }
  }, [hwid, loadData]);

  useEffect(() => {
    const hasActive = jobs.some((job) => ['pending', 'running'].includes(job.status));
    if (!hasActive) {
      return undefined;
    }
    const interval = setInterval(() => {
      loadData();
    }, 4000);
    return () => clearInterval(interval);
  }, [jobs, loadData]);

  function toggleProfile(profileId) {
    setSelected((current) => ({
      ...current,
      [profileId]: {
        checked: !current[profileId]?.checked,
        mode: current[profileId]?.mode || 'balanced',
        minutes: current[profileId]?.minutes || 15,
      },
    }));
  }

  async function startFarm() {
    try {
      setBusy(true);
      await api.startFarm({ hwid, items: selectedItems });
      await loadData();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось запустить ферму');
    } finally {
      setBusy(false);
    }
  }

  async function stopFarm() {
    try {
      setBusy(true);
      await api.stopFarm(hwid);
      await loadData();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось остановить ферму');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen testID="farm-screen">
      <Text style={[styles.title, { color: theme.textPrimary }]}>Ферма</Text>
      <Text style={[styles.subtitle, { color: theme.textSecondary }]}>Выберите несколько профилей и запустите параллельный прогрев в одном premium-пульте.</Text>

      <View style={[styles.heroCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.heroTitle, { color: theme.textPrimary }]}>Multi-profile control</Text>
        <Text style={[styles.heroText, { color: theme.textSecondary }]}>Подходит для быстрых запусков: отметьте профили, выберите режим и сразу смотрите логи внизу.</Text>
      </View>

      <View style={styles.actionRow}>
        <View style={styles.actionItem}>
          <ActionButton
            icon="play"
            label={busy ? 'Запуск...' : `Запустить (${selectedItems.length})`}
            onPress={startFarm}
            disabled={busy || selectedItems.length === 0}
            testID="start-farm-button"
          />
        </View>
        <View style={styles.actionItem}>
          <ActionButton icon="square" label="Стоп всем" onPress={stopFarm} disabled={busy} testID="stop-farm-button" variant="danger" />
        </View>
      </View>

      {error ? <Text style={[styles.error, { color: theme.danger }]}>{error}</Text> : null}

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator color={theme.primary} size="large" />
        </View>
      ) : (
        profiles.map((profile) => {
          const profileSelection = selected[profile.id] || { checked: false, mode: 'balanced', minutes: 15 };
          return (
            <View key={profile.id} style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]} testID={`farm-profile-card-${profile.id}`}>
              <View style={styles.headerRow}>
                <Pressable accessibilityRole="button" onPress={() => toggleProfile(profile.id)} style={styles.checkboxRow} testID={`farm-select-${profile.id}`}>
                  <View style={[styles.checkbox, { borderColor: theme.border, backgroundColor: profileSelection.checked ? theme.primary : 'transparent' }]} />
                  <View style={styles.flexItem}>
                    <Text style={[styles.profileName, { color: theme.textPrimary }]}>{profile.name}</Text>
                    <Text style={[styles.profileEmail, { color: theme.textSecondary }]}>{profile.email}</Text>
                  </View>
                </Pressable>
                <StatusPill label={profileSelection.mode.toUpperCase()} tone="success" testID={`farm-mode-pill-${profile.id}`} />
              </View>

              <View style={styles.modeRow}>
                {MODES.map((mode) => (
                  <View key={mode} style={styles.modeItem}>
                    <ActionButton
                      compact
                      icon="cpu"
                      label={mode}
                      onPress={() =>
                        setSelected((current) => ({
                          ...current,
                          [profile.id]: {
                            checked: current[profile.id]?.checked ?? true,
                            mode,
                            minutes: current[profile.id]?.minutes || 15,
                          },
                        }))
                      }
                      testID={`farm-mode-${profile.id}-${mode}`}
                      variant={profileSelection.mode === mode ? 'primary' : 'secondary'}
                    />
                  </View>
                ))}
              </View>
            </View>
          );
        })
      )}

      {jobs.map((job) => (
        <View key={job.id} style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]} testID={`farm-job-card-${job.id}`}>
          <View style={styles.headerRow}>
            <View style={styles.flexItem}>
              <Text style={[styles.profileName, { color: theme.textPrimary }]}>{job.profile_name}</Text>
              <Text style={[styles.profileEmail, { color: theme.textSecondary }]}>{job.current_action}</Text>
            </View>
            <StatusPill
              label={job.status.toUpperCase()}
              tone={job.status === 'running' ? 'success' : job.status === 'error' ? 'danger' : 'neutral'}
              testID={`farm-job-status-${job.id}`}
            />
          </View>
          <LogTerminal logs={job.logs} testID={`farm-job-log-${job.id}`} />
        </View>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    fontSize: 30,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  actionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  heroCard: {
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.md,
    gap: spacing.sm,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  heroText: {
    fontSize: 14,
    lineHeight: 20,
  },
  actionItem: {
    flex: 1,
  },
  error: {
    fontSize: 14,
    fontWeight: '600',
  },
  centered: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
  },
  card: {
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.md,
    gap: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
    alignItems: 'center',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    flex: 1,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1,
  },
  flexItem: {
    flex: 1,
    gap: 2,
  },
  profileName: {
    fontSize: 16,
    fontWeight: '700',
  },
  profileEmail: {
    fontSize: 13,
  },
  modeRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  modeItem: {
    flex: 1,
  },
});