export const palette = {
  dark: {
    background: '#09090B',
    surface: '#18181B',
    surfaceHighlight: '#27272A',
    border: '#27272A',
    borderFocus: '#3F3F46',
    textPrimary: '#FAFAFA',
    textSecondary: '#A1A1AA',
    primary: '#3B82F6',
    primaryActive: '#2563EB',
    success: '#10B981',
    successBg: 'rgba(16,185,129,0.12)',
    danger: '#EF4444',
    dangerBg: 'rgba(239,68,68,0.12)',
    warning: '#F59E0B',
    black: '#000000',
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const radii = {
  sm: 8,
  md: 12,
  lg: 18,
  pill: 999,
};

export function getTheme() {
  return palette.dark;
}
