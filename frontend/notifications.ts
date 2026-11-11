const dismissAfter = 4100;

function initializeNotification(notification: HTMLElement, onRemove: () => void) {
  const button = notification.querySelector<HTMLButtonElement>('[data-notification-close]');
  if (!button) return;

  const lifecycle = new AbortController();
  const options = { signal: lifecycle.signal };
  let remaining = dismissAfter;
  let timer: number | undefined;
  let startedAt = 0;
  let closing = false;
  let previousFocus: HTMLElement | undefined;

  function pause() {
    if (timer === undefined) return;
    window.clearTimeout(timer);
    timer = undefined;
    remaining = Math.max(0, remaining - (performance.now() - startedAt));
  }

  function remove() {
    pause();
    lifecycle.abort();
    notification.remove();
    onRemove();
  }

  function dismiss(manual: boolean) {
    if (closing) return;
    closing = true;
    pause();
    if (notification.contains(document.activeElement)) {
      if (previousFocus?.isConnected) {
        previousFocus.focus();
      } else {
        const heading = document.querySelector<HTMLElement>('main h1');
        if (heading) {
          heading.tabIndex = -1;
          heading.focus();
        }
      }
    }

    const { opacity, transform } = getComputedStyle(notification);
    notification.style.setProperty('--notification-from-opacity', opacity);
    notification.style.setProperty('--notification-from-transform', transform);
    notification.classList.add('notification--leaving');
    notification.classList.toggle('notification--manual', manual);
    notification.inert = true;
    const [animation] = notification.getAnimations();
    if (animation) void animation.finished.then(remove, remove);
    else remove();
  }

  function resume() {
    if (
      closing ||
      timer !== undefined ||
      document.hidden ||
      notification.matches(':hover, :focus-within') ||
      !notification.hasAttribute('data-auto-dismiss')
    ) {
      return;
    }

    startedAt = performance.now();
    timer = window.setTimeout(() => dismiss(false), remaining);
  }

  button.hidden = false;
  button.addEventListener('click', () => dismiss(true), options);
  notification.addEventListener('pointerenter', pause, options);
  notification.addEventListener('pointerleave', resume, options);
  notification.addEventListener(
    'focusin',
    (event) => {
      if (
        event.relatedTarget instanceof HTMLElement &&
        !notification.contains(event.relatedTarget)
      ) {
        previousFocus = event.relatedTarget;
      }
      pause();
    },
    options,
  );
  notification.addEventListener('focusout', () => queueMicrotask(resume), options);
  document.addEventListener(
    'visibilitychange',
    () => (document.hidden ? pause() : resume()),
    options,
  );
  window.addEventListener('pagehide', remove, options);
  resume();
}

export function initializeNotifications() {
  const viewport = document.querySelector('[data-notification-viewport]');
  if (!viewport) return;

  const announcement = viewport.querySelector('[data-notification-announcement]');
  for (const notification of viewport.querySelectorAll<HTMLElement>('[data-notification]')) {
    initializeNotification(notification, () => {
      if (!viewport.querySelector('[data-notification]')) viewport.remove();
    });
  }

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (announcement?.isConnected) {
        announcement.textContent = Array.from(
          viewport.querySelectorAll('[data-notification-text]'),
          (element) => element.textContent.trim(),
        ).join(' ');
      }
    });
  });
}
