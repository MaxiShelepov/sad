import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';

import { getTheme } from '../../src/theme';

const TAB_ICONS = {
  index: 'shield-checkmark-outline',
  profiles: 'people-outline',
  farm: 'albums-outline',
};

function renderTabIcon(routeName, color, size) {
  return <Ionicons color={color} name={TAB_ICONS[routeName] || 'ellipse-outline'} size={size} />;
}

export default function TabsLayout() {
  const theme = getTheme();

  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: theme.textPrimary,
        tabBarInactiveTintColor: theme.textSecondary,
        tabBarStyle: {
          position: 'absolute',
          left: 16,
          right: 16,
          bottom: 12,
          borderRadius: 24,
          backgroundColor: theme.surface,
          borderTopColor: 'transparent',
          height: 74,
          paddingTop: 8,
          paddingBottom: 10,
          borderWidth: 1,
          borderColor: theme.border,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '700',
        },
        tabBarIcon: ({ color, size }) => renderTabIcon(route.name, color, size),
      })}
    >
      <Tabs.Screen name="index" options={{ title: 'Лицензия' }} />
      <Tabs.Screen name="profiles" options={{ title: 'Профили' }} />
      <Tabs.Screen name="farm" options={{ title: 'Ферма' }} />
    </Tabs>
  );
}