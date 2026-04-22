import { useThemeStore } from '../../stores/themeStore';

export function useIsDark() {
  const { mode } = useThemeStore();
  return mode === 'dark';
}
