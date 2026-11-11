export function initializeCardPreview() {
  for (const preview of document.querySelectorAll<HTMLElement>('[data-card-preview]')) {
    const input = document.getElementById(preview.dataset.cardPreview ?? '');
    if (!(input instanceof HTMLTextAreaElement)) continue;

    const update = () => {
      preview.textContent = input.value || 'Пока пусто';
    };
    input.addEventListener('input', update);
    update();
  }
}
