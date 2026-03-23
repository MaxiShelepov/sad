import { StyleSheet, Text, View } from 'react-native';

import { getTheme, radii, spacing } from '../theme';

export function LogTerminal({ logs = [], testID }) {
  const theme = getTheme();

  function colorFor(level) {
    if (level === 'success') return theme.success;
    if (level === 'warning') return theme.warning;
    if (level === 'error') return theme.danger;
    if (level === 'operation') return theme.primary;
    return theme.textSecondary;
  }

  return (
    <View style={[styles.terminal, { borderColor: theme.border }]} testID={testID}>
      <Text style={[styles.title, { color: theme.textPrimary }]}>LOG</Text>
      {logs.length === 0 ? (
        <Text style={[styles.line, { color: theme.textSecondary }]}>Пока нет логов</Text>
      ) : (
        logs.slice(-12).map((log, index) => (
          <Text key={`${log.timestamp}-${index}`} style={[styles.line, { color: colorFor(log.level) }]}>
            [{new Date(log.timestamp).toLocaleTimeString()}] {log.message}
          </Text>
        ))
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  terminal: {
    backgroundColor: '#000000',
    borderRadius: radii.md,
    borderWidth: 1,
    padding: spacing.md,
    gap: 8,
  },
  title: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 1,
  },
  line: {
    fontSize: 12,
    lineHeight: 18,
    fontFamily: 'monospace',
  },
});
