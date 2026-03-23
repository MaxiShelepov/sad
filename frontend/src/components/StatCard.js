import { StyleSheet, Text, View } from 'react-native';

import { getTheme, radii, spacing } from '../theme';

export function StatCard({ label, value, accent = 'primary', testID }) {
  const theme = getTheme();
  const color = accent === 'success' ? theme.success : accent === 'warning' ? theme.warning : theme.primary;

  return (
    <View
      style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}
      testID={testID}
    >
      <Text style={[styles.label, { color: theme.textSecondary }]}>{label}</Text>
      <Text style={[styles.value, { color }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 92,
    borderRadius: radii.md,
    borderWidth: 1,
    padding: spacing.md,
    justifyContent: 'space-between',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  value: {
    fontSize: 24,
    fontWeight: '800',
  },
});
