import { Feather } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { getTheme, radii, spacing } from '../theme';
import { ActionButton } from './ActionButton';
import { StatusPill } from './StatusPill';

export function ProfileCard({ profile, onOpen, onDelete, testID }) {
  const theme = getTheme();
  const fingerprint = profile.fingerprint || {};

  return (
    <Animated.View
      entering={FadeInDown.duration(240)}
      style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border, shadowColor: theme.primary, shadowOpacity: 0.12, shadowRadius: 18, shadowOffset: { width: 0, height: 10 }, elevation: 4 }]}
      testID={testID}
    >
      <View style={styles.header}>
        <View style={styles.identityRow}>
          <View style={[styles.avatar, { backgroundColor: theme.surfaceHighlight, borderColor: theme.primarySoft }]}>
            <Feather color={theme.textPrimary} name="user" size={18} />
          </View>
          <View style={styles.grow}>
            <Text style={[styles.name, { color: theme.textPrimary }]} numberOfLines={1}>
              {profile.name}
            </Text>
            <Text style={[styles.email, { color: theme.textSecondary }]} numberOfLines={1}>
              {profile.email}
            </Text>
          </View>
        </View>
        <StatusPill label={profile.is_running ? 'В работе' : 'Готов'} tone={profile.is_running ? 'success' : 'neutral'} />
      </View>

      <View style={styles.infoRow}>
        <Text style={[styles.meta, { color: theme.textSecondary }]}>
          {fingerprint.browser} · {fingerprint.os_name} · {fingerprint.screen_width}x{fingerprint.screen_height}
        </Text>
        <Text style={[styles.meta, { color: theme.textSecondary }]} numberOfLines={1}>
          {profile.proxy || 'Без прокси'}
        </Text>
      </View>

      <View style={styles.statsRow}>
        <Text style={[styles.statText, { color: theme.textPrimary }]}>Trust {profile.stats?.trust_score ?? 0}</Text>
        <Text style={[styles.statText, { color: theme.textPrimary }]}>Операций {profile.stats?.total_operations ?? 0}</Text>
      </View>

      <View style={styles.actionsRow}>
        <View style={styles.actionItem}>
          <ActionButton compact icon="play" label="Открыть" onPress={onOpen} testID={`${testID}-open-button`} />
        </View>
        <View style={styles.actionItem}>
          <ActionButton
            compact
            icon="trash-2"
            label="Удалить"
            onPress={onDelete}
            testID={`${testID}-delete-button`}
            variant="danger"
          />
        </View>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radii.md,
    borderWidth: 1,
    padding: spacing.md,
    gap: spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  identityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: spacing.sm,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: radii.pill,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  grow: {
    flex: 1,
  },
  name: {
    fontSize: 17,
    fontWeight: '700',
  },
  email: {
    fontSize: 13,
    marginTop: 2,
  },
  infoRow: {
    gap: 6,
  },
  meta: {
    fontSize: 13,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: spacing.md,
  },
  statText: {
    fontSize: 13,
    fontWeight: '600',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionItem: {
    flex: 1,
  },
});
