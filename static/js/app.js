// Alpine / HTMX en local
import 'htmx.org';
import Alpine from 'alpinejs';

// Lucide icons (depuis NPM bundle)
import { createIcons } from "lucide";

window.Alpine = Alpine;
Alpine.start();

document.addEventListener("DOMContentLoaded", () => {
  try { createIcons(); } catch (e) {}
});

// CSRF pour HTMX (Django)
document.addEventListener('htmx:configRequest', (event) => {
  const csrftoken = document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1];
  if (csrftoken) event.detail.headers['X-CSRFToken'] = csrftoken;
});
