import { router, useFocusEffect } from 'expo-router';
import { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { api } from '../../src/api';
import { ActionButton } from '../../src/components/ActionButton';
import { ProfileCard } from '../../src/components/ProfileCard';
import { Screen } from '../../src/components/Screen';
import { SheetModal } from '../../src/components/SheetModal';
import { StatCard } from '../../src/components/StatCard';
import { useAppState } from '../../src/state/AppProvider';
import { getTheme, radii, spacing } from '../../src/theme';

const initialForm = {
  name: '',
  email: '',
  access_token: '',
  proxy: '',
  notes: '',
  use_browser: true,
  batch: '',
};

export default function ProfilesScreen() {
  const theme = getTheme();
  const { dashboard, hwid, refreshAll, subscription } = useAppState();
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [modalVisible, setModalVisible] = useState(false);
  const [form, setForm] = useState(initialForm);

  const availableSlots = useMemo(() => {
    const maxProfiles = subscription?.max_profiles ?? 0;
    return Math.max(maxProfiles - profiles.length, 0);
  }, [profiles.length, subscription?.max_profiles]);

  const loadProfiles = useCallback(async () => {
    if (!hwid) {
      return;
    }

    try {
      setLoading(true);
      const data = await api.getProfiles(hwid);
      setProfiles(data);
      setError('');
      refreshAll(hwid, true);
    } catch (requestError) {
      setError(requestError.message || 'Не удалось загрузить профили');
    } finally {
      setLoading(false);
    }
  }, [hwid, refreshAll]);

  useFocusEffect(
    useCallback(() => {
      loadProfiles();
    }, [loadProfiles]),
  );

  async function handleCreateOrImport() {
    try {
      setSaving(true);
      setError('');
      if (form.batch.trim()) {
        await api.importProfiles({ hwid, raw_text: form.batch });
      } else {
        await api.createProfile({ ...form, hwid });
      }
      setForm(initialForm);
      setModalVisible(false);
      await loadProfiles();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось сохранить профиль');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(profileId) {
    try {
      await api.deleteProfile(profileId, hwid);
      await loadProfiles();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось удалить профиль');
    }
  }

  return (
    <>
      <Screen testID="profiles-screen">
        <View style={styles.headerBlock}>
          <Text style={[styles.title, { color: theme.textPrimary }]}>Профили</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>Список аккаунтов, отпечатков и активных запусков.</Text>
        </View>

        <View style={styles.statsRow}>
          <StatCard label="Всего" value={profiles.length} accent="primary" testID="profiles-count-card" />
          <StatCard label="Доступно" value={availableSlots} accent="success" testID="profiles-available-card" />
        </View>

        <ActionButton icon="plus" label="Добавить или импортировать" onPress={() => setModalVisible(true)} testID="open-add-profile-button" />

        {error ? <Text style={[styles.error, { color: theme.danger }]}>{error}</Text> : null}

        {loading ? (
          <View style={styles.loadingBox}>
            <ActivityIndicator color={theme.primary} size="large" />
          </View>
        ) : profiles.length === 0 ? (
          <View style={[styles.emptyCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.emptyTitle, { color: theme.textPrimary }]}>Пока нет профилей</Text>
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>Добавьте один профиль или вставьте batch-список.</Text>
          </View>
        ) : (
          profiles.map((profile) => (
            <ProfileCard
              key={profile.id}
              onDelete={() => handleDelete(profile.id)}
              onOpen={() => router.push(`/profile/${profile.id}`)}
              profile={profile}
              testID={`profile-card-${profile.id}`}
            />
          ))
        )}
      </Screen>

      <SheetModal testID="profile-sheet-modal" title="Новый профиль" visible={modalVisible} onClose={() => setModalVisible(false)}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
          <View style={styles.formGroup}>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Имя профиля</Text>
            <TextInput
              onChangeText={(value) => setForm((current) => ({ ...current, name: value }))}
              placeholder="alpha"
              placeholderTextColor={theme.textSecondary}
              style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
              testID="profile-name-input"
              value={form.name}
            />
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Email</Text>
            <TextInput
              autoCapitalize="none"
              keyboardType="email-address"
              onChangeText={(value) => setForm((current) => ({ ...current, email: value }))}
              placeholder="mail@example.com"
              placeholderTextColor={theme.textSecondary}
              style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
              testID="profile-email-input"
              value={form.email}
            />
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Access token</Text>
            <TextInput
              autoCapitalize="none"
              onChangeText={(value) => setForm((current) => ({ ...current, access_token: value }))}
              placeholder="token"
              placeholderTextColor={theme.textSecondary}
              style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
              testID="profile-token-input"
              value={form.access_token}
            />
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Прокси</Text>
            <TextInput
              autoCapitalize="none"
              onChangeText={(value) => setForm((current) => ({ ...current, proxy: value }))}
              placeholder="http://user:pass@host:port"
              placeholderTextColor={theme.textSecondary}
              style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
              testID="profile-proxy-input"
              value={form.proxy}
            />
            <View style={styles.switchRow}>
              <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Использовать браузер</Text>
              <Switch
                onValueChange={(value) => setForm((current) => ({ ...current, use_browser: value }))}
                trackColor={{ false: theme.border, true: theme.primary }}
                value={form.use_browser}
              />
            </View>
            <Text style={[styles.inputLabel, { color: theme.textSecondary }]}>Batch-импорт (email|token|proxy)</Text>
            <TextInput
              multiline
              onChangeText={(value) => setForm((current) => ({ ...current, batch: value }))}
              placeholder="mail1@example.com|token1|proxy1"
              placeholderTextColor={theme.textSecondary}
              style={[styles.textarea, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.background }]}
              testID="profile-batch-input"
              textAlignVertical="top"
              value={form.batch}
            />
            <ActionButton
              disabled={saving || (!form.batch.trim() && (!form.name || !form.email))}
              icon="save"
              label={saving ? 'Сохранение...' : 'Сохранить'}
              onPress={handleCreateOrImport}
              testID="save-profile-button"
            />
          </View>
        </KeyboardAvoidingView>
      </SheetModal>
    </>
  );
}

const styles = StyleSheet.create({
  headerBlock: {
    gap: spacing.xs,
  },
  title: {
    fontSize: 30,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  error: {
    fontSize: 14,
    fontWeight: '600',
  },
  loadingBox: {
    paddingVertical: spacing.xl,
    alignItems: 'center',
  },
  emptyCard: {
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.lg,
    gap: spacing.sm,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '800',
  },
  emptyText: {
    fontSize: 15,
    lineHeight: 22,
  },
  formGroup: {
    gap: spacing.sm,
    paddingBottom: spacing.xl,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  input: {
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
  },
  textarea: {
    minHeight: 120,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
});