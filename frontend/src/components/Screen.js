import { ScrollView, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { getTheme, spacing } from '../theme';

export function Screen({ children, scroll = true, contentStyle, testID }) {
  const insets = useSafeAreaInsets();
  const theme = getTheme();

  const containerStyle = [
    styles.content,
    {
      paddingTop: insets.top + spacing.lg,
      paddingBottom: insets.bottom + spacing.lg,
    },
    contentStyle,
  ];

  return (
    <View style={[styles.root, { backgroundColor: theme.background }]} testID={testID}>
      <View style={[styles.glowOrbPrimary, { backgroundColor: theme.glowBlue }]} />
      <View style={[styles.glowOrbSecondary, { backgroundColor: theme.glowPurple }]} />
      {scroll ? (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={containerStyle}
          keyboardShouldPersistTaps="handled"
        >
          {children}
        </ScrollView>
      ) : (
        <View style={containerStyle}>{children}</View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    overflow: 'hidden',
  },
  content: {
    paddingHorizontal: spacing.md,
    gap: spacing.md,
  },
  glowOrbPrimary: {
    position: 'absolute',
    top: -80,
    right: -40,
    width: 220,
    height: 220,
    borderRadius: 999,
  },
  glowOrbSecondary: {
    position: 'absolute',
    bottom: 40,
    left: -80,
    width: 200,
    height: 200,
    borderRadius: 999,
  },
});
