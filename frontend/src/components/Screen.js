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
  },
  content: {
    paddingHorizontal: spacing.md,
    gap: spacing.md,
  },
});
