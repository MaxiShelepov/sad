import { Feather } from '@expo/vector-icons';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { getTheme, radii, spacing } from '../theme';

export function ActionButton({
  label,
  icon,
  onPress,
  variant = 'primary',
  disabled = false,
  testID,
  compact = false,
}) {
  const theme = getTheme();

  const toneStyles =
    variant === 'secondary'
      ? { backgroundColor: theme.surface, borderColor: theme.border, textColor: theme.textPrimary }
      : variant === 'danger'
        ? { backgroundColor: theme.dangerBg, borderColor: theme.danger, textColor: theme.danger }
        : { backgroundColor: theme.primary, borderColor: theme.primary, textColor: theme.textPrimary };

  return (
    <TouchableOpacity
      activeOpacity={0.82}
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[
        styles.button,
        compact && styles.compact,
        {
          backgroundColor: disabled ? theme.surfaceHighlight : toneStyles.backgroundColor,
          borderColor: toneStyles.borderColor,
          opacity: disabled ? 0.5 : 1,
        },
      ]}
      testID={testID}
    >
      <View style={styles.row}>
        {icon ? <Feather color={toneStyles.textColor} name={icon} size={18} /> : null}
        <Text style={[styles.label, { color: toneStyles.textColor }]}>{label}</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 52,
    borderRadius: radii.pill,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
  },
  compact: {
    minHeight: 46,
    paddingHorizontal: spacing.md,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
  },
});
