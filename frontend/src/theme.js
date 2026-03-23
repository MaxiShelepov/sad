export const palette = {
  dark: {
    background: '#050816',
    surface: '#0B1224',
    surfaceHighlight: '#111A33',
    border: '#1B2A4A',
    borderFocus: '#3E6FD8',
    textPrimary: '#F5F7FF',
    textSecondary: '#8FA4D1',
    primary: '#4EA1FF',
    primaryActive: '#2D7BFF',
    primarySoft: 'rgba(78,161,255,0.16)',
    secondary: '#9B5CFF',
    secondarySoft: 'rgba(155,92,255,0.16)',
    success: '#15E3A3',
    successBg: 'rgba(21,227,163,0.14)',
    danger: '#FF5D7A',
    dangerBg: 'rgba(255,93,122,0.14)',
    warning: '#FFBE55',
    warningBg: 'rgba(255,190,85,0.14)',
    glowBlue: 'rgba(78,161,255,0.22)',
    glowPurple: 'rgba(155,92,255,0.18)',
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
  md: 16,
  lg: 24,
  pill: 999,
};

export function getTheme() {
  return palette.dark;
}
