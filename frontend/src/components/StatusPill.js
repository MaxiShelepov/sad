import { StyleSheet, Text, View } from 'react-native';

import { getTheme, radii, spacing } from '../theme';

export function StatusPill({ label, tone = 'neutral', testID }) {
  const theme = getTheme();
  const colors =
    tone === 'success'
      ? { backgroundColor: theme.successBg, color: theme.success, borderColor: theme.success }
      : tone === 'danger'
        ? { backgroundColor: theme.dangerBg, color: theme.danger, borderColor: theme.danger }
        : { backgroundColor: theme.surfaceHighlight, color: theme.textSecondary, borderColor: theme.border };

  return (
    <View style={[styles.pill, colors]} testID={testID}>
      <Text style={[styles.label, { color: colors.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    borderRadius: radii.pill,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  label: {
    fontSize: 12,
    fontWeight: '700',
  },
});
