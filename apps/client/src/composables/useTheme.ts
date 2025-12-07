import { ref, watch, onMounted } from 'vue';

export type Theme = 'light' | 'dark';

const theme = ref<Theme>('dark');

export function useTheme() {
  const initTheme = () => {
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme') as Theme | null;
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      theme.value = savedTheme;
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme.value = prefersDark ? 'dark' : 'light';
    }
    applyTheme();
  };

  const applyTheme = () => {
    const root = document.documentElement;
    if (theme.value === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  };

  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', theme.value);
    applyTheme();
  };

  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme;
    localStorage.setItem('theme', theme.value);
    applyTheme();
  };

  const isDark = () => theme.value === 'dark';
  const isLight = () => theme.value === 'light';

  onMounted(() => {
    initTheme();
  });

  watch(theme, () => {
    applyTheme();
  });

  return {
    theme,
    toggleTheme,
    setTheme,
    isDark,
    isLight,
    initTheme
  };
}
