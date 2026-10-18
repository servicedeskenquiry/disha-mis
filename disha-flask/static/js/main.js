// ──────────────────────────────────────────────
// DISHA MIS – main.js
// Handles: language toggle, charts, file upload,
//          locked-module modal, step navigation
// ──────────────────────────────────────────────

// ── Translations ──
const LANG = {
  en: {
    // login
    ll_title:'Fisheries NGO<br>Management System',
    ll_sub:'Empowering fishermen communities across West Bengal',
    lc_title:'Welcome to DISHA',
    lc_sub:'Sign in to your account or continue as guest',
    lt_admin:'Admin / Staff', lt_bo:'Back Office',
    ll_user:'Username', ll_pass:'Password',
    ll_loginbtn:'Log In →',
    ll_guestbtn:'👁 Continue as Guest (View Only)',
    // sidebar / nav
    s_title:'Fisheries NGO MIS', s_sub:'Management Info System',
    s_logout:'⬅ Logout',
    nav_dashboard:'Dashboard', nav_submit:'Submit Report', nav_reports:'All Reports',
    nav_approval:'Approval Queue', nav_analytics:'Analytics', nav_export:'Export',
    nav_tags:'Issue Tags', nav_cases:'Case Studies', nav_schemes:'Govt. Schemes',
    nav_users:'User Profiles', nav_view_reports:'View Reports',
    sec_main:'Main', sec_reports:'Reports', sec_soon:'Coming Soon',
    sec_admin:'Admin', sec_public:'Public', sec_req_login:'Requires Login',
    mode_admin:'🟢 Admin Mode', mode_guest:'👁 Guest Mode',
    sw_to_guest:'👁 Switch to Guest View', sw_to_admin:'🔑 Log In as Admin',
    // dashboard
    d_heading:'Dashboard', d_sub:'Overview of DISHA MIS — September 2026',
    gb_title:'👁 You are in Guest Mode', gb_sub:'Log in to submit or manage reports.',
    pb_title:'System development in progress',
    pb_sub:'More modules coming — 5–6 weeks to full delivery', pb_complete:'Complete',
    st_total:'Total Reports', st_total_sub:'↑ 12 this month',
    st_pend:'Pending Approval', st_pend_admin:'⚠ Needs review', st_pend_guest:'Login to review',
    st_appr:'Approved', st_appr_sub:'80% approval rate',
    st_office:'Active Offices', st_office_sub:'Across districts',
    ch_monthly:'Monthly Reports', ch_status:'Status Breakdown',
    ch_office:'By Office', ch_activity:'Activity Types', ch_year:'This year',
    ct_recent:'Recent Submissions',
    th_office:'Office', th_act:'Activity', th_type:'Type', th_status:'Status', th_date:'Date',
    // submit
    sub_heading:'Submit Report', sub_sub:'Select report type and fill in the details',
    stp1:'Choose Type', stp2:'Fill Details', stp3:'Attachments', stp4:'Submit',
    rt_daily_title:'Daily Activity Report',
    rt_daily_desc:'Day-to-day field activities, meetings and community work',
    rt_quarter_title:'Quarter Report',
    rt_quarter_desc:'Quarterly summary of activities and outcomes',
    rt_annual_title:'Annual Report',
    rt_annual_desc:'Full year achievements, data and documentation',
    f_req:'Fill all required fields (*)', f_changetype:'← Change type',
    f_sec_details:'📋 Report Details', f_sec_attach:'📎 Attachments',
    fl_office:'Office / Branch *', fl_activity:'Activity Type *',
    fl_period:'Period *', fl_loc:'Location / Venue *',
    fl_participants:'No. of Participants', fl_by:'Submitted by',
    fl_desc:'Description *', fl_remarks:'Remarks',
    uz_title:'Click to attach or drag & drop', uz_sub:'JPG, PNG, PDF, DOC, DOCX',
    f_submit_btn:'📤 Submit for Approval', f_draft_btn:'💾 Save Draft',
    // reports
    rep_heading:'All Reports', rep_sub:'Click any row to view details',
    rf_all:'All', rf_daily:'📋 Daily', rf_quarter:'📊 Quarter', rf_annual:'📈 Annual',
    rth_office:'Office', rth_act:'Activity', rth_type:'Type',
    rth_period:'Period', rth_by:'By', rth_status:'Status',
    bl_title:'Login Required', bl_desc:'Log in to view all reports and details.',
    bl_btn:'Log In Now', rd_back:'← Back to list',
    dd_desc_label:'Description', dd_attach_label:'Attachments',
    dd_approval_label:'Approval Actions',
    dd_approval_msg:'🔒 Approval workflow is under development — coming soon.',
    // modal
    m_title:'Under Development', m_eta:'⏱ Available in 5–6 weeks', m_close:'Close',
    // lock messages
    lock_approval:'Approve, Query & Reject with comment thread.',
    lock_analytics:'Detailed charts with office & issue breakdown.',
    lock_export:'Export to Excel, PDF and Word.',
    lock_tags:'Link reports across periods by issue.',
    lock_cases:'Upload, view and download case documents.',
    lock_schemes:'Manage government scheme documents.',
    lock_users:'User roles and office assignment.',
    lock_submit_guest:'Log in to submit activity reports.',
    lock_approval_guest:'Log in to manage approvals.',
    lock_analytics_guest:'Log in to view detailed analytics.',
    lock_export_guest:'Log in to export reports.',
    lock_cases_guest:'Log in to access case studies.',
    lock_schemes_guest:'Log in to access scheme documents.',
    draft_saved:'Draft saved.',
  },
  bn: {
    ll_title:'মৎস্যজীবী এনজিও<br>ম্যানেজমেন্ট সিস্টেম',
    ll_sub:'পশ্চিমবঙ্গ জুড়ে মৎস্যজীবী সম্প্রদায়কে শক্তিশালী করা',
    lc_title:'DISHA-তে স্বাগতম',
    lc_sub:'আপনার অ্যাকাউন্টে লগইন করুন বা অতিথি হিসেবে প্রবেশ করুন',
    lt_admin:'অ্যাডমিন / স্টাফ', lt_bo:'ব্যাক অফিস',
    ll_user:'ব্যবহারকারীর নাম', ll_pass:'পাসওয়ার্ড',
    ll_loginbtn:'লগইন করুন →',
    ll_guestbtn:'👁 অতিথি হিসেবে প্রবেশ করুন (শুধু দেখুন)',
    s_title:'মৎস্যজীবী এনজিও MIS', s_sub:'ম্যানেজমেন্ট ইনফো সিস্টেম',
    s_logout:'⬅ লগআউট',
    nav_dashboard:'ড্যাশবোর্ড', nav_submit:'রিপোর্ট জমা দিন',
    nav_reports:'সব রিপোর্ট', nav_approval:'অনুমোদন তালিকা',
    nav_analytics:'বিশ্লেষণ', nav_export:'রপ্তানি',
    nav_tags:'ইস্যু ট্যাগ', nav_cases:'কেস স্টাডি',
    nav_schemes:'সরকারি প্রকল্প', nav_users:'ব্যবহারকারী প্রোফাইল',
    nav_view_reports:'রিপোর্ট দেখুন',
    sec_main:'প্রধান', sec_reports:'রিপোর্ট', sec_soon:'শীঘ্রই আসছে',
    sec_admin:'অ্যাডমিন', sec_public:'সর্বজনীন', sec_req_login:'লগইন প্রয়োজন',
    mode_admin:'🟢 অ্যাডমিন মোড', mode_guest:'👁 অতিথি মোড',
    sw_to_guest:'👁 অতিথি মোডে যান', sw_to_admin:'🔑 অ্যাডমিন হিসেবে লগইন',
    d_heading:'ড্যাশবোর্ড', d_sub:'DISHA MIS-এর সারসংক্ষেপ — সেপ্টেম্বর ২০২৬',
    gb_title:'👁 আপনি অতিথি মোডে আছেন',
    gb_sub:'রিপোর্ট জমা বা পরিচালনার জন্য লগইন করুন।',
    pb_title:'সিস্টেম উন্নয়ন চলছে',
    pb_sub:'আরও মডিউল আসছে — সম্পূর্ণ হতে ৫-৬ সপ্তাহ', pb_complete:'সম্পন্ন',
    st_total:'মোট রিপোর্ট', st_total_sub:'↑ এই মাসে ১২টি',
    st_pend:'অনুমোদন বাকি', st_pend_admin:'⚠ পর্যালোচনা প্রয়োজন',
    st_pend_guest:'দেখতে লগইন করুন',
    st_appr:'অনুমোদিত', st_appr_sub:'৮০% অনুমোদনের হার',
    st_office:'সক্রিয় অফিস', st_office_sub:'জেলা জুড়ে',
    ch_monthly:'মাসিক রিপোর্ট', ch_status:'স্ট্যাটাস বিশ্লেষণ',
    ch_office:'অফিস অনুযায়ী', ch_activity:'কার্যক্রমের ধরন', ch_year:'এই বছর',
    ct_recent:'সাম্প্রতিক জমা',
    th_office:'অফিস', th_act:'কার্যক্রম', th_type:'ধরন', th_status:'স্ট্যাটাস', th_date:'তারিখ',
    sub_heading:'রিপোর্ট জমা দিন',
    sub_sub:'রিপোর্টের ধরন বেছে নিন এবং তথ্য পূরণ করুন',
    stp1:'ধরন বাছুন', stp2:'তথ্য পূরণ', stp3:'সংযুক্তি', stp4:'জমা দিন',
    rt_daily_title:'দৈনিক কার্যক্রম রিপোর্ট',
    rt_daily_desc:'দিনের মাঠ কার্যক্রম, সভা ও কমিউনিটি কাজ',
    rt_quarter_title:'ত্রৈমাসিক রিপোর্ট',
    rt_quarter_desc:'ত্রৈমাসিক কার্যক্রম ও ফলাফলের সারসংক্ষেপ',
    rt_annual_title:'বার্ষিক রিপোর্ট',
    rt_annual_desc:'সম্পূর্ণ বছরের অর্জন, তথ্য ও ডকুমেন্টেশন',
    f_req:'সব প্রয়োজনীয় তথ্য (*) পূরণ করুন', f_changetype:'← ধরন পরিবর্তন',
    f_sec_details:'📋 রিপোর্টের তথ্য', f_sec_attach:'📎 সংযুক্তি',
    fl_office:'অফিস / শাখা *', fl_activity:'কার্যক্রমের ধরন *',
    fl_period:'সময়কাল *', fl_loc:'স্থান / ভেন্যু *',
    fl_participants:'অংশগ্রহণকারীর সংখ্যা', fl_by:'জমাকারীর নাম',
    fl_desc:'বিবরণ *', fl_remarks:'মন্তব্য',
    uz_title:'ক্লিক করুন বা ড্র্যাগ করুন', uz_sub:'JPG, PNG, PDF, DOC, DOCX',
    f_submit_btn:'📤 অনুমোদনের জন্য জমা দিন', f_draft_btn:'💾 খসড়া সংরক্ষণ',
    rep_heading:'সব রিপোর্ট',
    rep_sub:'বিস্তারিত দেখতে যেকোনো সারিতে ক্লিক করুন',
    rf_all:'সব', rf_daily:'📋 দৈনিক', rf_quarter:'📊 ত্রৈমাসিক', rf_annual:'📈 বার্ষিক',
    rth_office:'অফিস', rth_act:'কার্যক্রম', rth_type:'ধরন',
    rth_period:'সময়কাল', rth_by:'জমাকারী', rth_status:'স্ট্যাটাস',
    bl_title:'লগইন প্রয়োজন', bl_desc:'সব রিপোর্ট দেখতে লগইন করুন।',
    bl_btn:'এখন লগইন করুন', rd_back:'← তালিকায় ফিরুন',
    dd_desc_label:'বিবরণ', dd_attach_label:'সংযুক্তি',
    dd_approval_label:'অনুমোদনের পদক্ষেপ',
    dd_approval_msg:'🔒 অনুমোদন প্রক্রিয়া উন্নয়নাধীন — শীঘ্রই আসছে।',
    m_title:'উন্নয়নাধীন', m_eta:'⏱ ৫-৬ সপ্তাহের মধ্যে পাওয়া যাবে', m_close:'বন্ধ করুন',
    lock_approval:'অনুমোদন, জিজ্ঞাসা ও প্রত্যাখ্যান কমেন্ট সহ।',
    lock_analytics:'অফিস ও ইস্যু অনুযায়ী বিস্তারিত চার্ট।',
    lock_export:'এক্সেল, PDF ও Word-এ রপ্তানি।',
    lock_tags:'ইস্যু অনুযায়ী রিপোর্ট সংযুক্ত করুন।',
    lock_cases:'কেস ডকুমেন্ট আপলোড, দেখুন ও ডাউনলোড করুন।',
    lock_schemes:'সরকারি প্রকল্পের ডকুমেন্ট পরিচালনা।',
    lock_users:'ব্যবহারকারীর ভূমিকা ও অফিস নির্ধারণ।',
    lock_submit_guest:'রিপোর্ট জমা দিতে লগইন করুন।',
    lock_approval_guest:'অনুমোদন পরিচালনা করতে লগইন করুন।',
    lock_analytics_guest:'বিস্তারিত বিশ্লেষণ দেখতে লগইন করুন।',
    lock_export_guest:'রিপোর্ট রপ্তানি করতে লগইন করুন।',
    lock_cases_guest:'কেস স্টাডি দেখতে লগইন করুন।',
    lock_schemes_guest:'সরকারি প্রকল্প দেখতে লগইন করুন।',
    draft_saved:'খসড়া সংরক্ষিত হয়েছে।',
  }
};

let lang = localStorage.getItem('disha_lang') || 'en';
function T(key){ return (LANG[lang] || LANG.en)[key] || key; }

// ── Language toggle ──
function setLang(l) {
  lang = l;
  localStorage.setItem('disha_lang', l);
  document.querySelectorAll('.lang-btn, .ltl-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.lang === l);
  });
  applyTranslations();
}

const TRANSLATE_IDS = [
  'll-title','ll-sub','lc-title','lc-sub','lt-admin','lt-bo',
  'll-user','ll-pass','ll-loginbtn','ll-guestbtn',
  's-title','s-sub',
  'd-heading','d-sub','gb-title','gb-sub','gb-btn',
  'pb-title','pb-sub','pb-complete',
  'st-total','st-total-sub','st-pend','st-appr','st-appr-sub','st-office','st-office-sub',
  'ch-monthly','ch-status','ch-office','ch-activity','ch-year','ct-recent',
  'th-office','th-act','th-type','th-status','th-date',
  'sub-heading','sub-sub',
  'stp1','stp2','stp3','stp4',
  'rt-daily-title','rt-daily-desc','rt-quarter-title','rt-quarter-desc',
  'rt-annual-title','rt-annual-desc',
  'f-req','f-changetype','f-sec-details','f-sec-attach',
  'fl-office','fl-activity','fl-period','fl-loc','fl-participants','fl-by',
  'fl-desc','fl-remarks','uz-title','uz-sub','f-submit-btn','f-draft-btn',
  'rep-heading','rep-sub','rf-all','rf-daily','rf-quarter','rf-annual',
  'rth-office','rth-act','rth-type','rth-period','rth-by','rth-status',
  'bl-title','bl-desc','bl-btn','rd-back',
  'dd-desc-label','dd-attach-label','dd-approval-label','dd-approval-msg',
  'm-title','m-eta','m-close',
];

function applyTranslations() {
  TRANSLATE_IDS.forEach(htmlId => {
    const el = document.getElementById(htmlId);
    if (!el) return;
    const key = htmlId.replace(/-/g, '_');
    const val = LANG[lang][key];
    if (val === undefined) return;
    if (key === 'll_title' || key === 'll_sub') el.innerHTML = val;
    else el.textContent = val;
  });
  // placeholders
  const ph = {
    'f-loc':          lang === 'en' ? 'Village, Block, District'      : 'গ্রাম, ব্লক, জেলা',
    'f-ben':          lang === 'en' ? 'e.g. 45'                        : 'যেমন ৪৫',
    'f-by':           lang === 'en' ? 'Field officer name'             : 'মাঠ কর্মকর্তার নাম',
    'f-desc':         lang === 'en' ? 'Describe activity, outcomes…'   : 'কার্যক্রম, ফলাফল বর্ণনা করুন...',
    'f-remarks':      lang === 'en' ? 'Follow-up actions…'             : 'পরবর্তী পদক্ষেপ...',
  };
  Object.entries(ph).forEach(([id, p]) => {
    const el = document.getElementById(id);
    if (el) el.placeholder = p;
  });
}

// ── Locked module modal ──
function lock(msg) {
  const modal = document.getElementById('modal');
  if (!modal) return;
  document.getElementById('m-title').textContent = T('m_title');
  document.getElementById('modal-msg').textContent = msg;
  document.getElementById('m-eta').textContent = T('m_eta');
  document.getElementById('m-close').textContent = T('m_close');
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
  t._t = setTimeout(() => t.classList.remove('show'), 3000);
}

// ── Submit page step navigation ──
let selectedType = '';
let uploadedFiles = [];

function selectType(type, el) {
  selectedType = type;
  document.querySelectorAll('.rtype-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  const map = {
    daily:   ['📋', T('rt_daily_title')],
    quarter: ['📊', T('rt_quarter_title')],
    annual:  ['📈', T('rt_annual_title')],
  };
  const icon  = document.getElementById('form-type-icon');
  const label = document.getElementById('form-type-label');
  const rtypeInput = document.getElementById('rtype-input');
  if (icon)  icon.textContent  = map[type][0];
  if (label) label.textContent = map[type][1];
  if (rtypeInput) rtypeInput.value = type;

  const periodEl = document.getElementById('f-period');
  if (periodEl) {
    if (type === 'quarter')     periodEl.value = 'Q3 2026';
    else if (type === 'annual') periodEl.value = 'Annual 2026';
    else                        periodEl.value = new Date().toISOString().slice(0, 10);
  }
  const actGrp = document.getElementById('activity-group');
  if (actGrp) actGrp.style.display = type === 'daily' ? 'flex' : 'none';

  setTimeout(() => {
    const s1 = document.getElementById('step1');
    const s2 = document.getElementById('step2');
    if (s1) s1.style.display = 'none';
    if (s2) s2.style.display = 'block';
  }, 180);
}

function goBack() {
  const s1 = document.getElementById('step1');
  const s2 = document.getElementById('step2');
  if (s1) s1.style.display = 'block';
  if (s2) s2.style.display = 'none';
  uploadedFiles = [];
  const fp = document.getElementById('file-previews');
  if (fp) fp.innerHTML = '';
}

// ── File upload ──
function handleFiles(files) {
  Array.from(files).forEach(file => {
    if (file.size > 10 * 1024 * 1024) { showToast('File too large: ' + file.name); return; }
    const reader = new FileReader();
    reader.onload = e => {
      uploadedFiles.push({ name: file.name, size: file.size, type: file.type, data: e.target.result });
      renderPreviews();
    };
    reader.readAsDataURL(file);
  });
  const fi = document.getElementById('file-input');
  if (fi) fi.value = '';
}

function renderPreviews() {
  const fp = document.getElementById('file-previews');
  if (!fp) return;
  fp.innerHTML = uploadedFiles.map((f, i) => {
    const isImg = f.type.startsWith('image/');
    const sz = f.size > 1048576 ? (f.size / 1048576).toFixed(1) + 'MB' : Math.round(f.size / 1024) + 'KB';
    return `<div class="fp">
      ${isImg ? `<img src="${f.data}">` : `<div class="ficon">${f.type.includes('pdf') ? '📄' : '📝'}</div>`}
      <div class="fname">${f.name}</div>
      <div class="fsize">${sz}</div>
      <button class="fremove" onclick="removeFile(${i})">✕</button>
    </div>`;
  }).join('');
}

function removeFile(i) {
  uploadedFiles.splice(i, 1);
  renderPreviews();
}

// ── Drag & drop for upload zone ──
document.addEventListener('DOMContentLoaded', () => {
  // Apply saved language
  setLang(lang);

  // Set lang button active states
  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // Drag & drop
  const uz = document.getElementById('upload-zone');
  if (uz) {
    uz.addEventListener('dragover', e => { e.preventDefault(); uz.classList.add('drag'); });
    uz.addEventListener('dragleave', () => uz.classList.remove('drag'));
    uz.addEventListener('drop', e => {
      e.preventDefault();
      uz.classList.remove('drag');
      handleFiles(e.dataTransfer.files);
    });
  }

  // Flash messages auto-hide
  document.querySelectorAll('.flash-success, .flash-error').forEach(el => {
    setTimeout(() => el.style.opacity = '0', 4000);
    setTimeout(() => el.remove(), 4500);
  });
});

// ── Charts (Dashboard only) ──
function initCharts() {
  const barCtx = document.getElementById('barChart');
  if (barCtx) {
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep'],
        datasets: [{ data: [3,4,5,4,6,7,8,9,1], backgroundColor: 'rgba(45,158,101,.75)', borderRadius: 5, borderSkipped: false }]
      },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { size: 11 } } }, x: { grid: { display: false }, ticks: { font: { size: 11 } } } }
      }
    });
  }
  const pieCtx = document.getElementById('pieChart');
  if (pieCtx) {
    new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: ['Approved', 'Pending', 'Queried'],
        datasets: [{ data: [38,4,5], backgroundColor: ['#2d9e65','#e67e00','#1a5fa8'], borderWidth: 0, hoverOffset: 6 }]
      },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12, padding: 8 } } },
        cutout: '65%'
      }
    });
  }
  const offCtx = document.getElementById('officeChart');
  if (offCtx) {
    new Chart(offCtx, {
      type: 'bar',
      data: {
        labels: ['Kol N.','D.Harbour','Basirhat','Kakdwip','Canning','Sagar'],
        datasets: [{ data: [12,10,9,7,8,1], backgroundColor: 'rgba(26,95,168,.7)', borderRadius: 4, borderSkipped: false }]
      },
      options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: { grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { size: 11 } } }, y: { grid: { display: false }, ticks: { font: { size: 11 } } } }
      }
    });
  }
  const actCtx = document.getElementById('actChart');
  if (actCtx) {
    new Chart(actCtx, {
      type: 'bar',
      data: {
        labels: ['Community','Training','Campaign','Legal','Exposure','Deputation','Research','Conf.'],
        datasets: [{ data: [9,8,7,6,5,5,4,4], backgroundColor: 'rgba(184,120,0,.7)', borderRadius: 4, borderSkipped: false }]
      },
      options: { responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: 'rgba(0,0,0,.05)' }, ticks: { font: { size: 11 } } }, x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 30 } } }
      }
    });
  }
}

if (document.getElementById('barChart')) {
  if (typeof Chart !== 'undefined') initCharts();
  else window.addEventListener('load', initCharts);
}
