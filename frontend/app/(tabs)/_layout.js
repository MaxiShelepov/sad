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
          backgroundColor: theme.surface,
          borderTopColor: theme.border,
          height: 68,
          paddingTop: 8,
          paddingBottom: 8,
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