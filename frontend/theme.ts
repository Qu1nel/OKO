const themeMaxAge = 90 * 24 * 60 * 60;

type Theme = 'light' | 'dark';

function readTheme(cookiePrefix: string): Theme | undefined {
  const cookie = document.cookie
    .split(';')
    .map((part) => part.trim())
    .find((part) => part.startsWith(cookiePrefix));
  const value = cookie?.slice(cookiePrefix.length);
  if (value === 'light' || value === 'dark') return value;
}

export function initializeTheme() {
  const root = document.documentElement;
  const cookieName = root.dataset.themeCookie;
  if (!cookieName) return;

  const cookiePrefix = `${cookieName}=`;
  function saveTheme(theme: Theme) {
    root.dataset.theme = theme;
    document.cookie = `${cookiePrefix}${theme}; Path=/; Max-Age=${themeMaxAge}; SameSite=Strict`;
  }

  // Renew saved preferences, including the previous session-only cookie.
  const saved = readTheme(cookiePrefix);
  if (saved) saveTheme(saved);

  window.addEventListener('pageshow', (event) => {
    if (event.persisted) root.dataset.theme = readTheme(cookiePrefix) ?? 'light';
  });

  for (const toggle of document.querySelectorAll<HTMLButtonElement>('[data-theme-toggle]')) {
    toggle.addEventListener('click', () =>
      saveTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'),
    );
    toggle.hidden = false;
  }
}
