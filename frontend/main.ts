import './styles.css';

const toggle = document.querySelector<HTMLButtonElement>('[data-theme-toggle]');
const label = toggle?.querySelector('[data-theme-label]');

if (toggle && label) {
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const root = document.documentElement;
    const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = theme;
    label.textContent = theme === 'dark' ? 'Светлая тема' : 'Тёмная тема';
    document.cookie = `oko_theme=${theme}; Path=/; SameSite=Strict`;
  });
}
