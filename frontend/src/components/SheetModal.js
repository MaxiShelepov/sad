import { Feather } from '@expo/vector-icons';
import { KeyboardAvoidingView, Modal, Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { getTheme, radii, spacing } from '../theme';

export function SheetModal({ visible, title, onClose, children, testID }) {
  const theme = getTheme();

  return (
    <Modal animationType="slide" transparent visible={visible} onRequestClose={onClose}>
      <Pressable style={styles.overlay} onPress={onClose} testID={`${testID}-overlay`} />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.keyboard}>
        <View style={[styles.sheet, { backgroundColor: theme.surface, borderColor: theme.border }]} testID={testID}>
          <View style={styles.header}>
            <Text style={[styles.title, { color: theme.textPrimary }]}>{title}</Text>
            <Pressable accessibilityRole="button" hitSlop={10} onPress={onClose} testID={`${testID}-close-button`}>
              <Feather color={theme.textSecondary} name="x" size={20} />
            </Pressable>
          </View>
          {children}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.56)',
  },
  keyboard: {
    justifyContent: 'flex-end',
  },
  sheet: {
    minHeight: '55%',
    borderTopLeftRadius: radii.lg,
    borderTopRightRadius: radii.lg,
    borderWidth: 1,
    padding: spacing.md,
    gap: spacing.md,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
  },
});
