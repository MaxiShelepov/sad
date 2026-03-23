import * as Haptics from 'expo-haptics';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '../../../src/api';
import { ActionButton } from '../../../src/components/ActionButton';
import { Screen } from '../../../src/components/Screen';
import { getTheme, radii, spacing } from '../../../src/theme';

export default function FingerprintScreen() {
  const theme = getTheme();
  const { id, hwid } = useLocalSearchParams();
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;

    async function loadFingerprint() {
      try {
        const response = await api.getFingerprint(id, hwid);
        if (mounted) {
          setForm(response.fingerprint);
        }
      } catch (requestError) {
        if (mounted) {
          setError(requestError.message || 'Не удалось загрузить отпечаток');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadFingerprint();
    return () => {
      mounted = false;
    };
  }, [id, hwid]);

  async function saveFingerprint() {
    try {
      setSaving(true);
      await api.updateFingerprint(id, hwid, {
        browser: form.browser,
        browser_version: form.browser_version,
        os_name: form.os_name,
        os_category: form.os_category,
        platform: form.platform,
        screen_width: Number(form.screen_width),
        screen_height: Number(form.screen_height),
        timezone: form.timezone,
        webgl_vendor_group: form.webgl_vendor_group,
        webgl_renderer: form.webgl_renderer,
        user_agent: form.user_agent,
        connection_type: form.connection_type,
      });
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch (requestError) {
      setError(requestError.message || 'Не удалось сохранить отпечаток');
    } finally {
      setSaving(false);
    }
  }

  async function randomizeFingerprint() {
    try {
      setSaving(true);
      const updated = await api.randomizeFingerprint(id, hwid);
      setForm(updated.fingerprint);
    } catch (requestError) {
      setError(requestError.message || 'Не удалось обновить отпечаток');
    } finally {
      setSaving(false);
    }
  }

  if (loading || !form) {
    return (
      <Screen testID="fingerprint-loading-screen">
        <View style={styles.centered}>
          <ActivityIndicator color={theme.primary} size="large" />
        </View>
      </Screen>
    );
  }

  return (
    <Screen testID="fingerprint-screen">
      <ActionButton compact icon="arrow-left" label="Назад" onPress={() => router.back()} testID="fingerprint-back-button" variant="secondary" />
      <Text style={[styles.title, { color: theme.textPrimary }]}>Настройка отпечатка</Text>
      <Text style={[styles.subtitle, { color: theme.textSecondary }]}>Измените браузер, ОС, экран и GPU под мобильный профиль.</Text>

      <View style={[styles.heroCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.heroTitle, { color: theme.textPrimary }]}>Device identity editor</Text>
        <Text style={[styles.heroText, { color: theme.textSecondary }]}>Собирайте более правдоподобный мобильный отпечаток и сохраняйте его напрямую в ваш живой PHP/API backend.</Text>
      </View>

      <ActionButton icon="save" label={saving ? 'Сохранение...' : 'Сохранить сейчас'} onPress={saveFingerprint} disabled={saving} testID="save-fingerprint-top-button" />
      <ActionButton icon="shuffle" label="Случайный отпечаток" onPress={randomizeFingerprint} disabled={saving} testID="randomize-fingerprint-button" variant="secondary" />

      {[
        ['Браузер', 'browser'],
        ['Версия браузера', 'browser_version'],
        ['OS name', 'os_name'],
        ['OS category', 'os_category'],
        ['Platform', 'platform'],
        ['Ширина экрана', 'screen_width'],
        ['Высота экрана', 'screen_height'],
        ['Таймзона', 'timezone'],
        ['GPU group', 'webgl_vendor_group'],
        ['GPU renderer', 'webgl_renderer'],
        ['Connection', 'connection_type'],
        ['User-Agent', 'user_agent'],
      ].map(([label, key]) => (
        <View key={key} style={styles.fieldBlock}>
          <Text style={[styles.label, { color: theme.textSecondary }]}>{label}</Text>
          <TextInput
            onChangeText={(value) => setForm((current) => ({ ...current, [key]: value }))}
            placeholderTextColor={theme.textSecondary}
            style={[styles.input, { color: theme.textPrimary, borderColor: theme.border, backgroundColor: theme.surface }]}
            testID={`fingerprint-${key}-input`}
            value={String(form[key] ?? '')}
          />
        </View>
      ))}

      {error ? <Text style={[styles.error, { color: theme.danger }]}>{error}</Text> : null}

      <ActionButton icon="save" label={saving ? 'Сохранение...' : 'Сохранить'} onPress={saveFingerprint} disabled={saving} testID="save-fingerprint-button" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  centered: {
    paddingTop: spacing.xl,
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  fieldBlock: {
    gap: 6,
  },
  heroCard: {
    borderWidth: 1,
    borderRadius: radii.lg,
    padding: spacing.md,
    gap: spacing.sm,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  heroText: {
    fontSize: 14,
    lineHeight: 20,
  },
  label: {
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
  error: {
    fontSize: 14,
    fontWeight: '600',
  },
});
