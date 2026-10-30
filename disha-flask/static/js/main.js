// ──────────────────────────────────────────────
// DISHA MIS – main.js
// Handles: language toggle, charts, submit form,
//          attachments, locked-module modal
// ──────────────────────────────────────────────

// ── Language ──
// Pages are rendered in English. Elements marked data-t are translated by
// looking up their English text in BN (static/js/i18n_bn.js); data-tp does
// the same for placeholders. Missing entries stay in English.
let lang = 'en';
try { lang = localStorage.getItem('disha_lang') || 'en'; } catch (e) {}

function tr(s) {
  if (lang !== 'bn' || typeof BN === 'undefined') return s;
  return BN[s] !== undefined ? BN[s] : s;
}
const T = tr;

function setLang(l) {
  lang = l;
  try { localStorage.setItem('disha_lang', l); } catch (e) {}
  document.documentElement.lang = l === 'bn' ? 'bn' : 'en';
  document.querySelectorAll('[data-lang]').forEach(b => b.classList.toggle('active', b.dataset.lang === l));
  applyTranslations();
  refreshCharts();
}

function applyTranslations() {
  document.querySelectorAll('[data-t]').forEach(el => {
    if (el.dataset.en === undefined) el.dataset.en = el.textContent.trim();
    el.textContent = tr(el.dataset.en);
  });
  document.querySelectorAll('[data-tp]').forEach(el => {
    if (el.dataset.enPh === undefined) el.dataset.enPh = el.placeholder;
    el.placeholder = tr(el.dataset.enPh);
  });
}

// ── Locked module modal ──
function lock(msg) {
  const modal = document.getElementById('modal');
  if (!modal) return;
  document.getElementById('modal-msg').textContent = tr(msg);
  modal.classList.add('open');
}
function closeModal() {
  const modal = document.getElementById('modal');
  if (modal) modal.classList.remove('open');
}

// ── Toast ──
function showToast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  document.getElementById('toast-msg').textContent = msg;
  t.classList.add('show');
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove('show'), 3500);
}

// ──────────────────────────────────────────────
// Submit report
// ──────────────────────────────────────────────
function selectType(type, el, instant) {
  document.querySelectorAll('.rtype-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  const meta = (typeof TYPE_META !== 'undefined' ? TYPE_META : []).find(t => t.key === type) || {};
  const icon = document.getElementById('form-type-icon');
  const label = document.getElementById('form-type-label');
  if (icon) icon.textContent = meta.icon || '📋';
  if (label) { label.dataset.en = meta.label || ''; label.textContent = tr(meta.label || ''); }
  document.getElementById('rtype-input').value = type;

  const periodic = type !== 'daily';
  // Head Office and "Consolidated" are only for periodic reports
  document.querySelectorAll('.periodic-only').forEach(o => { o.hidden = !periodic; o.disabled = !periodic; });
  ['f-district', 'f-activity'].forEach(id => {
    const s = document.getElementById(id);
    if (s && s.selectedOptions[0] && s.selectedOptions[0].disabled) s.value = '';
  });
  // Date for Daily, Period for the rest
  document.querySelectorAll('.period-group').forEach(g => {
    const on = g.dataset.for === type;
    g.style.display = on ? '' : 'none';
    g.querySelectorAll('input,select').forEach(i => { i.disabled = !on; });
  });
  const dateEl = document.getElementById('f-date');
  if (dateEl) {
    dateEl.required = !periodic;
    if (!periodic && !dateEl.value) dateEl.value = new Date().toISOString().slice(0, 10);
  }
  showTemplate(document.getElementById('f-activity').value);
  updatePlaces();

  const go = () => {
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
  };
  instant ? go() : setTimeout(go, 150);
}

function goBack() {
  document.getElementById('step1').style.display = 'block';
  document.getElementById('step2').style.display = 'none';
}

// Open the format/template that belongs to the chosen activity type
function showTemplate(activity) {
  document.querySelectorAll('.activity-template').forEach(t => {
    const on = t.dataset.activity === activity;
    t.style.display = on ? '' : 'none';
    t.querySelectorAll('input,textarea,select').forEach(i => { i.disabled = !on; });
  });
}

function togglePcat(cb) {
  const num = cb.closest('.p-item').querySelector('input[type=number]');
  num.disabled = !cb.checked;
  if (cb.checked) num.focus(); else num.value = '';
  cb.closest('.p-item').classList.toggle('on', cb.checked);
}

// Fill Total from Women + Men when Total is empty
document.addEventListener('input', e => {
  if (!e.target.name || !['p_women', 'p_men'].includes(e.target.name)) return;
  const total = document.getElementById('p-total');
  if (!total || total.dataset.touched) return;
  const w = +document.querySelector('[name=p_women]').value || 0;
  const m = +document.querySelector('[name=p_men]').value || 0;
  total.value = (w + m) || '';
});
document.addEventListener('change', e => {
  if (e.target.id === 'p-total') e.target.dataset.touched = e.target.value ? '1' : '';
});

// ── Attachments (two categories, shared limit) ──
const picked = {};   // category -> DataTransfer

function attachTotal() {
  let n = Object.values(picked).reduce((s, dt) => s + dt.files.length, 0);
  n += document.querySelectorAll('input[name=archive_ref]:checked').length;
  n += document.querySelectorAll('input[name=keep_file]:checked').length;
  return n;
}

function updateAttachCount() {
  const el = document.getElementById('attach-count');
  if (!el) return;
  const n = attachTotal();
  el.textContent = n;
  el.parentElement.classList.toggle('over', n > MAX_ATTACH);
  document.querySelectorAll('input[name=archive_ref]').forEach(cb => {
    if (!cb.checked) cb.disabled = n >= MAX_ATTACH;
  });
}

function addFiles(cat, input) {
  const dt = picked[cat] || (picked[cat] = new DataTransfer());
  Array.from(input.files).forEach(file => {
    if (attachTotal() >= MAX_ATTACH) { showToast(tr('Maximum attachments reached') + ` (${MAX_ATTACH})`); return; }
    if (file.size > MAX_FILE_MB * 1024 * 1024) { showToast(tr('File too large') + ': ' + file.name); return; }
    dt.items.add(file);
  });
  input.files = dt.files;
  renderPreviews(cat);
  updateAttachCount();
}

function removeFile(cat, i) {
  const old = picked[cat];
  const dt = new DataTransfer();
  Array.from(old.files).forEach((f, j) => { if (j !== i) dt.items.add(f); });
  picked[cat] = dt;
  document.getElementById('files-' + cat).files = dt.files;
  renderPreviews(cat);
  updateAttachCount();
}

function renderPreviews(cat) {
  const box = document.getElementById('previews-' + cat);
  if (!box) return;
  box.innerHTML = '';
  Array.from(picked[cat].files).forEach((f, i) => {
    const div = document.createElement('div');
    div.className = 'fp';
    const sz = f.size > 1048576 ? (f.size / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(f.size / 1024)) + ' KB';
    if (f.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(f);
      div.appendChild(img);
    } else {
      const ic = document.createElement('div');
      ic.className = 'ficon';
      ic.textContent = f.type.startsWith('video/') ? '🎬' : f.type.includes('pdf') ? '📄' : '📝';
      div.appendChild(ic);
    }
    const nm = document.createElement('div'); nm.className = 'fname'; nm.textContent = f.name;
    const s = document.createElement('div'); s.className = 'fsize'; s.textContent = sz;
    const rm = document.createElement('button');
    rm.type = 'button'; rm.className = 'fremove'; rm.textContent = '✕';
    rm.onclick = () => removeFile(cat, i);
    div.append(nm, s, rm);
    box.appendChild(div);
  });
}

function filterArchive(q) {
  q = q.toLowerCase();
  document.querySelectorAll('.archive-item').forEach(el => {
    el.style.display = el.dataset.search.includes(q) ? '' : 'none';
  });
}

// ──────────────────────────────────────────────
// Charts – every chart prints its values on the bars/slices
// ──────────────────────────────────────────────
const PALETTE = ['#2d9e65', '#1a5fa8', '#b87800', '#7b2fa8', '#c0392b', '#0e8a8a', '#6b8c77', '#e67e00'];
const CHARTS = [];   // {chart, labels, datasets}

function onChartsReady(fn) {
  if (typeof Chart === 'undefined') return;
  if (typeof ChartDataLabels !== 'undefined') Chart.register(ChartDataLabels);
  Chart.defaults.font.family = "'Segoe UI', 'Noto Sans Bengali', sans-serif";
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
  else fn();
}

function wrap(label, max) {
  const words = String(label).split(' ');
  const lines = [''];
  words.forEach(w => {
    if ((lines[lines.length - 1] + ' ' + w).trim().length > max) lines.push(w);
    else lines[lines.length - 1] = (lines[lines.length - 1] + ' ' + w).trim();
  });
  return lines;
}

function barChart(id, labels, datasets, opt = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  const horizontal = !!opt.horizontal;
  const valueAxis = horizontal ? 'x' : 'y';
  const catAxis = horizontal ? 'y' : 'x';
  const fmtLabel = l => opt.wrapLabels ? wrap(tr(l), 14) : tr(l);
  const ds = datasets.map((d, i) => ({
    label: d.label,
    data: d.data,
    backgroundColor: d.color || (datasets.length > 1 ? PALETTE[i % PALETTE.length] : 'rgba(45,158,101,.8)'),
    borderRadius: 4,
    borderSkipped: false,
    stack: opt.stacked ? 's' : undefined,
  }));
  const totals = labels.map((_, i) => datasets.reduce((s, d) => s + (d.data[i] || 0), 0));
  const chart = new Chart(el, {
    type: 'bar',
    data: { labels: labels.map(fmtLabel), datasets: ds.map(d => ({ ...d, label: tr(d.label) })) },
    options: {
      responsive: true, maintainAspectRatio: false, indexAxis: horizontal ? 'y' : 'x',
      layout: { padding: { top: horizontal ? 0 : 18, right: horizontal ? 28 : 0 } },
      plugins: {
        legend: { display: !!opt.legend, position: 'bottom',
                  labels: { boxWidth: 10, font: { size: 11 },
                            generateLabels: opt.shortLegend ? shortLegend : undefined } },
        datalabels: {
          // stacked: value inside each segment + total on top; otherwise value at the end of the bar
          display: ctx => ctx.dataset.data[ctx.dataIndex] > 0,
          anchor: opt.stacked ? 'center' : 'end',
          align: opt.stacked ? 'center' : 'end',
          offset: 2,
          color: opt.stacked ? '#fff' : '#1a2e22',
          font: { size: 11, weight: '600' },
          formatter: v => v,
        },
      },
      scales: {
        [valueAxis]: { beginAtZero: true, stacked: !!opt.stacked, grid: { color: 'rgba(0,0,0,.05)' },
                       ticks: { precision: 0, font: { size: 11 } } },
        [catAxis]: { stacked: !!opt.stacked, grid: { display: false },
                     ticks: { font: { size: 11 }, autoSkip: false } },
      },
    },
    plugins: opt.totals && opt.stacked ? [stackTotals(totals)] : [],
  });
  CHARTS.push({ chart, labels, datasets, fmtLabel });
}

function shortLegend(chart) {
  const ov = Chart.overrides[chart.config.type];
  const gen = (ov && ov.plugins && ov.plugins.legend && ov.plugins.legend.labels.generateLabels)
    || Chart.defaults.plugins.legend.labels.generateLabels;
  return gen(chart).map(l => {
    if (l.text && l.text.length > 22) l.text = l.text.slice(0, 20) + '…';
    return l;
  });
}

// Prints the stack total above each stacked column
function stackTotals(totals) {
  return {
    id: 'stackTotals',
    afterDatasetsDraw(chart) {
      const { ctx } = chart;
      const meta = chart.getDatasetMeta(chart.data.datasets.length - 1);
      ctx.save();
      ctx.font = '600 11px "Segoe UI", sans-serif';
      ctx.fillStyle = '#1a2e22';
      ctx.textAlign = 'center';
      totals.forEach((t, i) => {
        if (!t) return;
        let top = Infinity;
        chart.data.datasets.forEach((_, di) => {
          const m = chart.getDatasetMeta(di);
          if (!m.hidden && m.data[i]) top = Math.min(top, m.data[i].y);
        });
        if (top !== Infinity) ctx.fillText(t, meta.data[i].x, top - 5);
      });
      ctx.restore();
    },
  };
}

function doughnutChart(id, labels, data, colors, opt = {}) {
  const el = document.getElementById(id);
  if (!el) return;
  const total = data.reduce((a, b) => a + b, 0);
  const chart = new Chart(el, {
    type: 'doughnut',
    data: { labels: labels.map(tr), datasets: [{ data, backgroundColor: colors, borderWidth: 1, borderColor: '#fff' }] },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '55%',
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 }, generateLabels: shortLegend } },
        datalabels: {
          display: ctx => ctx.dataset.data[ctx.dataIndex] > 0,
          color: '#fff', font: { size: 12, weight: '700' },
          formatter: v => opt.percent && total ? `${v}\n${Math.round(100 * v / total)}%` : v,
          textAlign: 'center',
        },
      },
    },
  });
  CHARTS.push({ chart, labels, datasets: null, fmtLabel: tr });
}

function refreshCharts() {
  CHARTS.forEach(c => {
    c.chart.data.labels = c.labels.map(c.fmtLabel);
    if (c.datasets) c.chart.data.datasets.forEach((d, i) => { d.label = tr(c.datasets[i].label); });
    c.chart.update('none');
  });
}

// ── Page init ──
document.addEventListener('DOMContentLoaded', () => {
  setLang(lang);

  // Drag & drop onto upload zones
  document.querySelectorAll('.upload-zone').forEach(uz => {
    const input = uz.querySelector('input[type=file]');
    uz.addEventListener('dragover', e => { e.preventDefault(); uz.classList.add('drag'); });
    uz.addEventListener('dragleave', () => uz.classList.remove('drag'));
    uz.addEventListener('drop', e => {
      e.preventDefault();
      uz.classList.remove('drag');
      const dt = new DataTransfer();
      Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
      input.files = dt.files;
      addFiles(uz.dataset.cat, input);
    });
  });

  // Success messages fade out; errors stay until the next page
  document.querySelectorAll('.flash-success').forEach(el => {
    setTimeout(() => { el.style.opacity = '0'; }, 5000);
    setTimeout(() => el.remove(), 5500);
  });
});

// ──────────────────────────────────────────────
// Phase 3: Block / GP / Village, issue tree, duplicate check
// ──────────────────────────────────────────────
function updatePlaces() {
  if (typeof PLACES === 'undefined') return;
  const district = (document.getElementById('f-district') || {}).value || '';
  const lists = PLACES[district] || {};
  ['block', 'gp', 'village'].forEach(k => {
    const dl = document.getElementById('dl-' + k);
    if (!dl) return;
    dl.innerHTML = '';
    (lists[k] || []).forEach(v => { const o = document.createElement('option'); o.value = v; dl.appendChild(o); });
  });
  // Block is required for Daily reports of a district (not Head Office)
  const rtype = (document.getElementById('rtype-input') || {}).value;
  const block = document.getElementById('f-block');
  const need = rtype === 'daily' && district !== 'Head Office';
  if (block) block.required = need;
  document.querySelectorAll('.daily-req').forEach(s => { s.style.display = need ? '' : 'none'; });
}

// Ticking a subject ticks its issue; unticking an issue clears what is below it
function tagToggle(cb) {
  const box = cb.closest('.tt-issue, .tt-subject');
  if (cb.checked) {
    let el = cb.closest('.tt-children');
    while (el) {
      const parentBox = el.parentElement;
      const parentCb = parentBox && parentBox.querySelector(':scope > label input[type=checkbox]');
      if (parentCb) parentCb.checked = true;
      el = parentBox ? parentBox.closest('.tt-children') : null;
    }
  } else if (box && box.querySelector(':scope > label input') === cb) {
    box.querySelectorAll('.tt-children input[type=checkbox]').forEach(i => { i.checked = false; });
  }
  refreshTagTree();
}

function refreshTagTree() {
  document.querySelectorAll('.tt-issue, .tt-subject').forEach(box => {
    const own = box.querySelector(':scope > label input[type=checkbox]');
    box.classList.toggle('open', !!(own && own.checked));
  });
}

let dupChecked = false;
function initReportForm() {
  const form = document.getElementById('report-form');
  if (!form) return;
  const district = document.getElementById('f-district');
  if (district) district.addEventListener('change', updatePlaces);
  updatePlaces();
  refreshTagTree();

  form.addEventListener('submit', async e => {
    if (dupChecked || document.getElementById('confirm-dup').value === '1') return;
    // At least one issue tag
    if (!form.querySelector('input[name=tagpath]:checked')) {
      e.preventDefault();
      alertBox(tr('Please select at least one Issue tag.'));
      return;
    }
    e.preventDefault();
    const fd = new FormData(form);
    for (const k of [...fd.keys()]) if (k.startsWith('files_')) fd.delete(k);
    if (REPORT_ID) fd.set('report_id', REPORT_ID);
    let dups = [];
    try {
      const r = await fetch(DUP_URL, { method: 'POST', body: fd, credentials: 'same-origin' });
      if (r.ok) dups = await r.json();
    } catch (_) { /* network hiccup: the server checks again */ }
    if (!dups.length) { dupChecked = true; form.submit(); return; }
    const list = document.getElementById('dup-list');
    list.innerHTML = '';
    dups.forEach(d => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = '/reports/' + d.id; a.target = '_blank'; a.textContent = '#' + d.id;
      li.appendChild(a);
      li.appendChild(document.createTextNode(` · ${d.district} · ${d.period}${d.village ? ' · ' + d.village : ''} · ${d.submitted_by} · ${tr(d.status)}`));
      list.appendChild(li);
    });
    const box = document.getElementById('dup-box');
    box.hidden = false;
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
}

function submitAnyway() {
  document.getElementById('confirm-dup').value = '1';
  dupChecked = true;
  document.getElementById('report-form').submit();
}

function alertBox(msg) {
  let el = document.getElementById('form-alert');
  const form = document.getElementById('report-form');
  if (!el) {
    el = document.createElement('div');
    el.id = 'form-alert'; el.className = 'flash-error';
    form.querySelector('.tag-tree').before(el);
  }
  el.textContent = '⚠ ' + msg;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
