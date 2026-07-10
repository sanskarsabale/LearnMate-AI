/**
 * ============================================================
 * LearnMate AI — Main JavaScript
 * Global utilities: theme toggle, AI response formatter,
 * toast notifications, misc UX helpers.
 * ============================================================
 */

/* ── Theme Management ─────────────────────────────────────── */
(function initTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
})();

function updateThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (!icon) return;
  icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
}

document.getElementById('themeToggle')?.addEventListener('click', function () {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next    = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeIcon(next);

  // Persist to server (non-blocking)
  fetch('/settings', {
    method:  'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body:    `action=theme&theme=${next}`,
  }).catch(() => {});
});

/* ── AI Response Formatter ────────────────────────────────── */
/**
 * Converts plain AI text (with markdown) to safe HTML.
 * Handles: **bold**, *italic*, `code`, code blocks, lists, headers.
 */
function formatAIResponse(text) {
  if (!text) return '';

  // Escape HTML first (safety)
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (```lang\n...\n```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h6 class="fw-bold mt-3 mb-1">$1</h6>');
  html = html.replace(/^## (.+)$/gm,  '<h5 class="fw-bold mt-3 mb-1">$1</h5>');
  html = html.replace(/^# (.+)$/gm,   '<h4 class="fw-bold mt-3 mb-1">$1</h4>');

  // Bold + italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g,          '<em>$1</em>');

  // Numbered lists
  html = html.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, '<ol class="ps-4 mb-2">$1</ol>');

  // Bullet lists
  html = html.replace(/^[-•]\s(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)(?!\s*<li>)/g, '<ul class="ps-4 mb-2">$1</ul>');

  // Line breaks → paragraphs
  html = html
    .split(/\n\n+/)
    .map(p => p.trim())
    .filter(p => p && !p.startsWith('<h') && !p.startsWith('<pre') && !p.startsWith('<ol') && !p.startsWith('<ul'))
    .map(p => `<p class="mb-2">${p.replace(/\n/g, '<br>')}</p>`)
    .join('') + html.split(/\n\n+/).filter(p => p.startsWith('<')).join('');

  return html;
}

/* ── Toast Notifications ──────────────────────────────────── */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position:fixed;bottom:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(container);
  }
  const icons = { success: 'check-circle-fill', danger: 'x-circle-fill', info: 'info-circle-fill', warning: 'exclamation-triangle-fill' };
  const toast = document.createElement('div');
  toast.className = `alert alert-${type} d-flex align-items-center gap-2 fade-in`;
  toast.style.cssText = 'min-width:260px;max-width:360px;box-shadow:0 4px 20px rgba(0,0,0,0.15);';
  toast.innerHTML = `<i class="bi bi-${icons[type] || 'info-circle-fill'}"></i><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transition = 'opacity 0.3s'; setTimeout(() => toast.remove(), 300); }, 4000);
}

/* ── Auto-dismiss flash alerts ────────────────────────────── */
document.querySelectorAll('.alert:not(.lm-ai-alert)').forEach(alert => {
  setTimeout(() => {
    alert.classList.remove('show');
    setTimeout(() => alert.remove(), 200);
  }, 5000);
});

/* ── Animate stat cards on scroll ────────────────────────── */
const observerOpts = { threshold: 0.15 };
const statsObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('fade-in');
      statsObserver.unobserve(e.target);
    }
  });
}, observerOpts);
document.querySelectorAll('.stat-card, .glass-card').forEach(el => statsObserver.observe(el));

/* ── Global CSRF helper (for Flask-WTF if needed) ─────────── */
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

/* ── Jinja filter polyfill: from_json ──────────────────────── */
// Used in templates that call  |from_json — handled server-side via custom filter.
// This JS function is a no-op placeholder for clarity.

/* ── Confirm before delete ────────────────────────────────── */
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  });
});
