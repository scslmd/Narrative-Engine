import { useThemeStore } from '../../stores/themeStore';
import { resolveEffectiveMode } from '../../theme/theme';

export function useIsDark() {
  const { mode, _systemTick } = useThemeStore();
  // Subscribe to _systemTick so components re-render when OS theme changes
  void _systemTick;
  return resolveEffectiveMode(mode) === 'dark';
}
