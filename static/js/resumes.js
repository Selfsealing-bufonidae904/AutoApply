/* ═══════════════════════════════════════════════════════════════
   RESUME LIBRARY — browse, preview, and download AI-generated resumes
   Implements: FR-115 (library UI), FR-116 (detail view), FR-117 (app link)
   ═══════════════════════════════════════════════════════════════ */
import { apiFetch, escHtml } from './api.js';
import { t, _applyDataI18n } from './i18n.js';

let currentPage = 1;
let currentPerPage = 50;
let searchTimeout = null;

/* ── Metrics cards ─────────────────────────────────────────── */

async function loadResumeMetrics() {
  const container = document.getElementById('resume-metrics');
  if (!container) return;
  try {
    const data = await apiFetch('/api/resumes/metrics');
    container.innerHTML = `
      <div class="summary-card" role="group" aria-label="${escHtml(t('resumes.total_versions'))}">
        <div class="summary-value">${data.total_versions}</div>
        <div class="summary-label" data-i18n="resumes.total_versions">${escHtml(t('resumes.total_versions'))}</div>
      </div>
      <div class="summary-card" role="group" aria-label="${escHtml(t('resumes.tailored_rate'))}">
        <div class="summary-value">${data.tailored_interview_rate}%</div>
        <div class="summary-label" data-i18n="resumes.tailored_rate">${escHtml(t('resumes.tailored_rate'))}</div>
      </div>
      <div class="summary-card" role="group" aria-label="${escHtml(t('resumes.fallback_rate'))}">
        <div class="summary-value">${data.fallback_interview_rate}%</div>
        <div class="summary-label" data-i18n="resumes.fallback_rate">${escHtml(t('resumes.fallback_rate'))}</div>
      </div>
      <div class="summary-card" role="group" aria-label="${escHtml(t('resumes.avg_score_interview'))}">
        <div class="summary-value">${data.avg_score_interviewed}</div>
        <div class="summary-label" data-i18n="resumes.avg_score_interview">${escHtml(t('resumes.avg_score_interview'))}</div>
      </div>
    `;
    _applyDataI18n(container);
  } catch {
    container.innerHTML = '';
  }
}

/* ── Resume list ───────────────────────────────────────────── */

export async function loadResumes(page) {
  if (page !== undefined) currentPage = page;

  const listEl = document.getElementById('resume-list');
  const paginationEl = document.getElementById('resume-pagination');
  if (!listEl) return;

  const searchInput = document.getElementById('resume-search');
  const sortSelect = document.getElementById('resume-sort');
  const search = searchInput ? searchInput.value.trim() : '';
  const sort = sortSelect ? sortSelect.value : 'created_at';

  listEl.innerHTML = `<p class="text-muted" data-i18n="resumes.loading">${escHtml(t('resumes.loading'))}</p>`;

  try {
    const params = new URLSearchParams({
      page: currentPage, per_page: currentPerPage, sort, order: 'desc',
    });
    if (search) params.set('search', search);

    const data = await apiFetch(`/api/resumes?${params}`);
    loadResumeMetrics();

    if (!data.items || data.items.length === 0) {
      listEl.innerHTML = `<p class="analytics-empty" data-i18n="resumes.empty">${escHtml(t('resumes.empty'))}</p>`;
      if (paginationEl) paginationEl.innerHTML = '';
      _applyDataI18n(listEl);
      return;
    }

    const rows = data.items.map(item => `
      <tr>
        <td>${escHtml(item.company)}</td>
        <td>${escHtml(item.job_title)}</td>
        <td>${item.match_score ?? '-'}</td>
        <td>${escHtml((item.created_at || '').slice(0, 10))}</td>
        <td><span class="status-mini-badge status-${escHtml(item.application_status || 'unknown')}">${escHtml(item.application_status || '-')}</span></td>
        <td>${escHtml(item.llm_provider || t('resumes.no_provider'))}</td>
        <td>
          <button type="button" class="btn btn-sm btn-primary" onclick="viewResume(${item.id})"
                  aria-label="${escHtml(t('resumes.view'))} ${escHtml(item.company)}"
                  data-i18n="resumes.view">${escHtml(t('resumes.view'))}</button>
          ${item.resume_pdf_exists ? `<button type="button" class="btn btn-sm btn-secondary" onclick="downloadResume(${item.id})"
                  aria-label="${escHtml(t('resumes.download'))} ${escHtml(item.company)}"
                  data-i18n="resumes.download">${escHtml(t('resumes.download'))}</button>` : ''}
        </td>
      </tr>
    `).join('');

    listEl.innerHTML = `
      <table class="analytics-table" role="table" aria-label="${escHtml(t('resumes.title'))}">
        <thead>
          <tr>
            <th data-i18n="resumes.col_company">${escHtml(t('resumes.col_company'))}</th>
            <th data-i18n="resumes.col_job_title">${escHtml(t('resumes.col_job_title'))}</th>
            <th data-i18n="resumes.col_score">${escHtml(t('resumes.col_score'))}</th>
            <th data-i18n="resumes.col_date">${escHtml(t('resumes.col_date'))}</th>
            <th data-i18n="resumes.col_status">${escHtml(t('resumes.col_status'))}</th>
            <th data-i18n="resumes.col_provider">${escHtml(t('resumes.col_provider'))}</th>
            <th data-i18n="resumes.col_actions">${escHtml(t('resumes.col_actions'))}</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
    _applyDataI18n(listEl);

    // Pagination
    const totalPages = Math.ceil(data.total_count / currentPerPage);
    if (paginationEl && totalPages > 1) {
      const pageInfo = t('resumes.page_info')
        .replace('{page}', currentPage)
        .replace('{total}', totalPages);
      paginationEl.innerHTML = `
        <button type="button" class="btn btn-sm btn-secondary" onclick="switchResumePage(${currentPage - 1})"
                ${currentPage <= 1 ? 'disabled' : ''} data-i18n="resumes.prev_page">${escHtml(t('resumes.prev_page'))}</button>
        <span class="resume-page-info">${escHtml(pageInfo)}</span>
        <button type="button" class="btn btn-sm btn-secondary" onclick="switchResumePage(${currentPage + 1})"
                ${currentPage >= totalPages ? 'disabled' : ''} data-i18n="resumes.next_page">${escHtml(t('resumes.next_page'))}</button>
      `;
      _applyDataI18n(paginationEl);
    } else if (paginationEl) {
      paginationEl.innerHTML = '';
    }
  } catch {
    listEl.innerHTML = `<p class="text-danger" data-i18n="resumes.error_loading">${escHtml(t('resumes.error_loading'))}</p>`;
    _applyDataI18n(listEl);
  }
}

/* ── Detail view ───────────────────────────────────────────── */

export async function viewResume(id) {
  const overlay = document.getElementById('resume-detail-overlay');
  const content = document.getElementById('resume-detail-content');
  if (!overlay || !content) return;

  content.innerHTML = `<p data-i18n="resumes.loading">${escHtml(t('resumes.loading'))}</p>`;
  overlay.classList.remove('hidden');

  try {
    const data = await apiFetch(`/api/resumes/${id}`);

    const mdContent = data.resume_md_content
      ? escHtml(data.resume_md_content).replace(/\n/g, '<br>')
      : '';

    content.innerHTML = `
      <div class="resume-detail-meta">
        <div class="resume-meta-item">
          <strong data-i18n="resumes.col_company">${escHtml(t('resumes.col_company'))}</strong>
          <span>${escHtml(data.company)}</span>
        </div>
        <div class="resume-meta-item">
          <strong data-i18n="resumes.col_job_title">${escHtml(t('resumes.col_job_title'))}</strong>
          <span>${escHtml(data.job_title)}</span>
        </div>
        <div class="resume-meta-item">
          <strong data-i18n="resumes.match_score">${escHtml(t('resumes.match_score'))}</strong>
          <span>${data.match_score ?? '-'}</span>
        </div>
        <div class="resume-meta-item">
          <strong data-i18n="resumes.generated_on">${escHtml(t('resumes.generated_on'))}</strong>
          <span>${escHtml((data.created_at || '').slice(0, 10))}</span>
        </div>
        <div class="resume-meta-item">
          <strong data-i18n="resumes.ai_model">${escHtml(t('resumes.ai_model'))}</strong>
          <span>${escHtml(data.llm_provider || '')} ${escHtml(data.llm_model || '')}</span>
        </div>
        <div class="resume-meta-item">
          <strong data-i18n="resumes.col_status">${escHtml(t('resumes.col_status'))}</strong>
          <span class="status-mini-badge status-${escHtml(data.application_status || 'unknown')}">${escHtml(data.application_status || '-')}</span>
        </div>
      </div>

      <div class="resume-detail-actions">
        ${data.resume_pdf_exists ? `
          <button type="button" class="btn btn-primary" onclick="previewResumePdf(${id})"
                  data-i18n="resumes.view_pdf">${escHtml(t('resumes.view_pdf'))}</button>
          <button type="button" class="btn btn-secondary" onclick="downloadResume(${id})"
                  data-i18n="resumes.download_pdf">${escHtml(t('resumes.download_pdf'))}</button>
        ` : `<p class="text-muted" data-i18n="resumes.file_missing">${escHtml(t('resumes.file_missing'))}</p>`}
        ${data.application_id ? `
          <button type="button" class="btn btn-secondary" onclick="closeResumeDetail(); window.viewApplication && window.viewApplication(${data.application_id})"
                  data-i18n="resumes.view_application">${escHtml(t('resumes.view_application'))}</button>
        ` : ''}
      </div>

      ${data.file_missing ? `<p class="text-danger" data-i18n="resumes.file_missing">${escHtml(t('resumes.file_missing'))}</p>` : ''}

      <div id="resume-pdf-container" class="resume-pdf-embed hidden"></div>

      ${mdContent ? `
        <div class="resume-detail-content">
          <h3 data-i18n="resumes.metadata">${escHtml(t('resumes.metadata'))}</h3>
          <div class="resume-md-rendered">${mdContent}</div>
        </div>
      ` : ''}
    `;
    _applyDataI18n(content);
  } catch {
    content.innerHTML = `<p class="text-danger" data-i18n="resumes.error_loading">${escHtml(t('resumes.error_loading'))}</p>`;
    _applyDataI18n(content);
  }
}

export function closeResumeDetail() {
  const overlay = document.getElementById('resume-detail-overlay');
  if (overlay) overlay.classList.add('hidden');
  const pdfContainer = document.getElementById('resume-pdf-container');
  if (pdfContainer) {
    pdfContainer.innerHTML = '';
    pdfContainer.classList.add('hidden');
  }
}

export function previewResumePdf(id) {
  const container = document.getElementById('resume-pdf-container');
  if (!container) return;
  const token = window.__apiToken || '';
  container.innerHTML = `<iframe src="/api/resumes/${id}/pdf" title="Resume PDF preview"
    style="width:100%;height:600px;border:1px solid var(--border-color,#333);border-radius:8px;"
    ></iframe>`;
  container.classList.remove('hidden');
}

export function downloadResume(id) {
  const token = window.__apiToken || '';
  const link = document.createElement('a');
  link.href = `/api/resumes/${id}/pdf?download=true`;
  link.download = `resume_${id}.pdf`;
  link.click();
}

export function switchResumePage(page) {
  if (page < 1) return;
  loadResumes(page);
}

/* ── Init search listener ──────────────────────────────────── */

export function initResumeSearch() {
  const searchInput = document.getElementById('resume-search');
  const sortSelect = document.getElementById('resume-sort');

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => loadResumes(1), 300);
    });
  }
  if (sortSelect) {
    sortSelect.addEventListener('change', () => loadResumes(1));
  }
}
