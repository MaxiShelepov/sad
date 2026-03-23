import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { ActionButton } from '../../src/components/ActionButton';
import { Screen } from '../../src/components/Screen';
import { StatCard } from '../../src/components/StatCard';
import { StatusPill } from '../../src/components/StatusPill';
import { useAppState } from '../../src/state/AppProvider';
import { getTheme, radii, spacing } from '../../src/theme';

export default function LicenseScreen() {
  const theme = getTheme();
  const { dashboard, error, hwid, loading, refreshing, subscription, refreshAll } = useAppState();

  async function copyHwid() {
    await Clipboard.setStringAsync(hwid);
    await Haptics.selectionAsync();
  }

  return (
    <Screen testID="license-screen">
      <View style={styles.hero}>
        <Text style={[styles.kicker, { color: theme.textSecondary }]}>WLESS PRO</Text>
        <Text style={[styles.title, { color: theme.textPrimary }]}>Премиальный мобильный центр управления</Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>Лицензия, профили, fingerprint и прогрев — в одном Android-интерфейсе.</Text>
      </View>

      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]} testID="license-card">
        <View style={styles.rowBetween}>
          <View style={styles.flexItem}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>HWID</Text>
            <Text style={[styles.hwid, { color: theme.textPrimary }]} testID="hwid-value">
              {hwid || 'Генерация...'}
            </Text>
          </View>
          <ActionButton compact icon="copy" label="Копировать" onPress={copyHwid} testID="copy-hwid-button" />
        </View>

        <View style={styles.rowBetween}>
          <View style={styles.flexItem}>
            <Text style={[styles.label, { color: theme.textSecondary }]}>Статус подписки</Text>
            <Text style={[styles.plan, { color: theme.textPrimary }]}>
              {subscription?.plan_name || 'Загрузка...'}
            </Text>
            <Text style={[styles.note, { color: theme.textSecondary }]}>{subscription?.message || 'Проверяем лицензию'}</Text>
          </View>
          <StatusPill
            label={subscription?.active ? 'Активна' : 'Неактивна'}
            tone={subscription?.active ? 'success' : 'danger'}
            testID="license-status-pill"
          />
        </View>

        <View style={styles.statsGrid}>
          <StatCard label="Дней осталось" value={subscription?.days_left ?? 0} accent="primary" testID="days-left-card" />
          <StatCard label="Профилей" value={dashboard?.profiles_total ?? 0} accent="success" testID="profiles-total-card" />
        </View>

        <View style={styles.statsGrid}>
          <StatCard label="В работе" value={dashboard?.profiles_running ?? 0} accent="warning" testID="profiles-running-card" />
          <StatCard label="Активных задач" value={dashboard?.active_jobs ?? 0} accent="primary" testID="active-jobs-card" />
        </View>

        {error ? <Text style={[styles.error, { color: theme.danger }]}>{error}</Text> : null}

        <ActionButton
          icon="refresh-cw"
          label={refreshing || loading ? 'Обновление...' : 'Проверить снова'}
          onPress={() => refreshAll()}
          disabled={refreshing || loading}
          testID="refresh-license-button"
        />
        <ActionButton
          icon="arrow-right"
          label="Перейти к профилям"
          onPress={() => {
            Haptics.selectionAsync();
            router.push('/(tabs)/profiles');
          }}
          disabled={!subscription?.active}
          testID="go-to-profiles-button"
          variant="secondary"
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: spacing.sm,
  },
  kicker: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.4,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    lineHeight: 38,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
  },
  card: {
    borderRadius: radii.lg,
    borderWidth: 1,
    padding: spacing.md,
    gap: spacing.md,
    shadowColor: '#4EA1FF',
    shadowOpacity: 0.14,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 14 },
    elevation: 6,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: spacing.md,
  },
  flexItem: {
    flex: 1,
    gap: 6,
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  hwid: {
    fontSize: 15,
    fontWeight: '700',
  },
  plan: {
    fontSize: 22,
    fontWeight: '800',
  },
  note: {
    fontSize: 14,
    lineHeight: 20,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  error: {
    fontSize: 14,
    fontWeight: '600',
  },
});
