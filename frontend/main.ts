import './styles.css';

const check = document.querySelector<HTMLButtonElement>('[data-check]');
const status = document.querySelector<HTMLParagraphElement>('[data-status]');
const theme = document.querySelector<HTMLButtonElement>('[data-theme-toggle]');

if (check && status && theme) {
  let checks = 0;
  check.disabled = false;
  theme.disabled = false;
  status.textContent = 'Страница готова к проверке.';

  check.addEventListener('click', () => {
    checks += 1;
    status.textContent = `Отклик получен: ${checks}.`;
  });

  theme.addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme !== 'dark';
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    theme.setAttribute('aria-pressed', String(dark));
  });
}
