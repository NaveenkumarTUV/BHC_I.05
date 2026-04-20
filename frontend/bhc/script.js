"use strict";

const state = {
  pending: [],
  pendingFiltered: [],
  processed: [],
  processedFiltered: [],
  processedSync: {},
  excelStatus: null,
  session: { authenticated: false, is_admin: false, must_change_password: false },
  adminConfig: null,
  selected: null,
  generatedQuote: null,
  activeTab: "overview",
  isAutoRefreshing: false,
  autoRefreshTimer: null,
  // DEQ module
  deqRecords: [],
  deqFiltered: [],
  deqSync: {},
  deqBhcClients: [],
  deqSections: [],
};

const AUTO_REFRESH_MS = 15000;
const API_TIMEOUT_MS = 45000;
const API_GET_RETRY_COUNT = 1;
const SESSION_CHECK_INTERVAL_MS = 60000;
const TAB_STORAGE_KEY = "bhc_active_tab";

const el = {
  navUser: () => document.getElementById("nav-user"),
  btnProfileMenu: () => document.getElementById("btn-profile-menu"),
  profileMenu: () => document.getElementById("profile-menu"),
  authPanel: () => document.getElementById("auth-panel"),
  dashboardShell: () => document.getElementById("dashboard-shell"),
  btnRefresh: () => document.getElementById("btn-refresh"),
  btnExport: () => document.getElementById("btn-export"),
  btnLogout: () => document.getElementById("btn-logout"),
  loginEmail: () => document.getElementById("login-email"),
  loginPassword: () => document.getElementById("login-password"),
  btnLogin: () => document.getElementById("btn-login"),
  btnForgotPasswordToggle: () => document.getElementById("btn-forgot-password-toggle"),
  forgotPasswordPanel: () => document.getElementById("forgot-password-panel"),
  forgotEmail: () => document.getElementById("forgot-email"),
  forgotStepEmail: () => document.getElementById("forgot-step-email"),
  forgotStepAnswer: () => document.getElementById("forgot-step-answer"),
  btnForgotLookup: () => document.getElementById("btn-forgot-lookup"),
  btnForgotBack: () => document.getElementById("btn-forgot-back"),
  forgotQuestionLabel: () => document.getElementById("forgot-question-label"),
  forgotAnswer: () => document.getElementById("forgot-answer"),
  forgotNewPassword: () => document.getElementById("forgot-new-password"),
  forgotConfirmPassword: () => document.getElementById("forgot-confirm-password"),
  btnForgotPassword: () => document.getElementById("btn-forgot-password"),
  authFeedback: () => document.getElementById("auth-feedback"),
  loginFormSection: () => document.getElementById("login-form-section"),
  registerFormSection: () => document.getElementById("register-form-section"),
  authDivider: () => document.querySelector(".auth-divider span"),
  btnAuthToggle: () => document.getElementById("btn-auth-toggle"),
  authToggleText: () => document.getElementById("auth-toggle-text"),
  regFullName: () => document.getElementById("reg-full-name"),
  regEmail: () => document.getElementById("reg-email"),
  regDesignation: () => document.getElementById("reg-designation"),
  regPassword: () => document.getElementById("reg-password"),
  regConfirmPassword: () => document.getElementById("reg-confirm-password"),
  regPasswordPolicy: () => document.getElementById("reg-password-policy"),
  regPolicyLength: () => document.getElementById("reg-policy-length"),
  regPolicyUpper: () => document.getElementById("reg-policy-upper"),
  regPolicyLower: () => document.getElementById("reg-policy-lower"),
  regPolicyDigit: () => document.getElementById("reg-policy-digit"),
  regPolicySpecial: () => document.getElementById("reg-policy-special"),
  regPolicyMatch: () => document.getElementById("reg-policy-match"),
  regSecurityQuestion: () => document.getElementById("reg-security-question"),
  regSecurityAnswer: () => document.getElementById("reg-security-answer"),
  btnRegister: () => document.getElementById("btn-register"),
  profileDesignation: () => document.getElementById("profile-designation"),
  profileSignatureFile: () => document.getElementById("profile-signature-file"),
  profileSignatureStatus: () => document.getElementById("profile-signature-status"),
  profileSecurityQuestion: () => document.getElementById("profile-security-question"),
  profileSecurityAnswer: () => document.getElementById("profile-security-answer"),
  profileSqStatus: () => document.getElementById("profile-sq-status"),
  btnSaveProfile: () => document.getElementById("btn-save-profile"),
  excelSourceBadge: () => document.getElementById("excel-source-badge"),
  excelSourceName: () => document.getElementById("excel-source-name"),
  excelSourcePath: () => document.getElementById("excel-source-path"),

  tabs: () => document.querySelectorAll(".section-tab"),
  tabPanels: () => document.querySelectorAll(".tab-panel"),
  jumpTabButtons: () => document.querySelectorAll("[data-jump-tab]"),
  adminTabButton: () => document.querySelector('.section-tab[data-tab="admin"]'),

  mTotal: () => document.getElementById("m-total"),
  mPending: () => document.getElementById("m-pending"),
  mQuoted: () => document.getElementById("m-quoted"),
  mConverted: () => document.getElementById("m-converted"),
  mQuotedRevenue: () => document.getElementById("m-quoted-revenue"),
  mConvertedRevenue: () => document.getElementById("m-converted-revenue"),
  heroPending: () => document.getElementById("hero-pending"),
  heroQuoted: () => document.getElementById("hero-quoted"),

  pendingCount: () => document.getElementById("pending-count"),
  pendingSearch: () => document.getElementById("pending-search"),
  pendingPropertyFilter: () => document.getElementById("pending-property-filter"),
  pendingBody: () => document.getElementById("pending-body"),

  detailEmpty: () => document.getElementById("detail-empty"),
  detailPanel: () => document.getElementById("detail-panel"),
  dName: () => document.getElementById("d-name"),
  dPhone: () => document.getElementById("d-phone"),
  dLocation: () => document.getElementById("d-location"),
  dProperty: () => document.getElementById("d-property"),
  dStructure: () => document.getElementById("d-structure"),
  dStructurePreview: () => document.getElementById("d-structure-preview"),
  dArea: () => document.getElementById("d-area"),
  dIssue: () => document.getElementById("d-issue"),
  dPrice: () => document.getElementById("d-price"),
  dRef: () => document.getElementById("d-ref"),
  discountPercent: () => document.getElementById("discount-percent"),

  dServiceName: () => document.getElementById("d-service-name"),

  btnGenerate: () => document.getElementById("btn-generate"),
  btnDownloadPdf: () => document.getElementById("btn-download-pdf"),
  btnSendEmail: () => document.getElementById("btn-send-email"),
  detailFeedback: () => document.getElementById("detail-feedback"),

  pdfPreviewModal: () => document.getElementById("pdf-preview-modal"),
  pdfPreviewFrame: () => document.getElementById("pdf-preview-frame"),
  previewLoading: () => document.getElementById("preview-loading"),
  previewClose: () => document.getElementById("preview-close"),
  previewCancel: () => document.getElementById("preview-cancel"),
  previewInsertSig: () => document.getElementById("preview-insert-sig"),
  previewFeedback: () => document.getElementById("preview-feedback"),

  processedCount: () => document.getElementById("processed-count"),
  processedSearch: () => document.getElementById("processed-search"),
  processedStatusFilter: () => document.getElementById("processed-status-filter"),
  processedPaymentFilter: () => document.getElementById("processed-payment-filter"),
  processedPropertyFilter: () => document.getElementById("processed-property-filter"),
  processedDateFrom: () => document.getElementById("processed-date-from"),
  processedDateTo: () => document.getElementById("processed-date-to"),
  processedBody: () => document.getElementById("processed-body"),

  accountEmail: () => document.getElementById("account-email"),
  btnOpenPasswordPanel: () => document.getElementById("btn-open-password-panel"),
  profilePasswordPanel: () => document.getElementById("profile-password-panel"),
  profilePasswordActions: () => document.getElementById("profile-password-actions"),
  changeCurrentPassword: () => document.getElementById("change-current-password"),
  changeNewPassword: () => document.getElementById("change-new-password"),
  changeConfirmPassword: () => document.getElementById("change-confirm-password"),
  btnChangePassword: () => document.getElementById("btn-change-password"),
  accountFeedback: () => document.getElementById("account-feedback"),
  passwordStrength: () => document.getElementById("password-strength"),
  policyLength: () => document.getElementById("policy-length"),
  policyUpper: () => document.getElementById("policy-upper"),
  policyLower: () => document.getElementById("policy-lower"),
  policyDigit: () => document.getElementById("policy-digit"),
  policySpecial: () => document.getElementById("policy-special"),
  policyDifferent: () => document.getElementById("policy-different"),
  policyMatch: () => document.getElementById("policy-match"),
  passwordToggles: () => document.querySelectorAll(".password-toggle"),

  adminDbPath: () => document.getElementById("admin-db-path"),
  adminLoginCard: () => document.getElementById("admin-login-card"),
  adminConfigCard: () => document.getElementById("admin-config-card"),
  adminLoginHelp: () => document.getElementById("admin-login-help"),
  btnSaveCompany: () => document.getElementById("btn-save-company"),
  btnAddPricingRow: () => document.getElementById("btn-add-pricing-row"),
  btnAddNewBuildingPricingRow: () => document.getElementById("btn-add-new-building-pricing-row"),
  btnSavePricing: () => document.getElementById("btn-save-pricing"),
  btnSaveDocument: () => document.getElementById("btn-save-document"),
  btnCreateUser: () => document.getElementById("btn-create-user"),
  adminPricingBody: () => document.getElementById("admin-pricing-body"),
  adminNewBuildingPricingBody: () => document.getElementById("admin-new-building-pricing-body"),
  adminUsersBody: () => document.getElementById("admin-users-body"),

  adminFeedback: () => document.getElementById("admin-feedback"),

  btnLoadAudit: () => document.getElementById("btn-load-audit"),
  auditFilterType: () => document.getElementById("audit-filter-type"),
  auditLogBody: () => document.getElementById("audit-log-body"),
  auditLogWrap: () => document.getElementById("audit-log-wrap"),
  auditLogEmpty: () => document.getElementById("audit-log-empty"),
  auditLogCount: () => document.getElementById("audit-log-count"),

  adminCompanyName: () => document.getElementById("admin-company-name"),
  adminCompanySubtitle: () => document.getElementById("admin-company-subtitle"),
  adminCompanyAddress: () => document.getElementById("admin-company-address"),
  adminCompanyPhone: () => document.getElementById("admin-company-phone"),
  adminCompanyEmail: () => document.getElementById("admin-company-email"),
  adminContactName: () => document.getElementById("admin-contact-name"),
  adminCompanyProfile: () => document.getElementById("admin-company-profile"),
  adminTuvHistory: () => document.getElementById("admin-tuv-history"),
  adminServiceCapabilities: () => document.getElementById("admin-service-capabilities"),
  adminDeliverables: () => document.getElementById("admin-deliverables"),
  adminPaymentTerms: () => document.getElementById("admin-payment-terms"),
  adminOtherTerms: () => document.getElementById("admin-other-terms"),
  adminSystemNote: () => document.getElementById("admin-system-note"),
  adminUserFullName: () => document.getElementById("admin-user-full-name"),
  adminUserDesignation: () => document.getElementById("admin-user-designation"),
  adminUserEmail: () => document.getElementById("admin-user-email"),
  adminUserPassword: () => document.getElementById("admin-user-password"),
  adminUserSignature: () => document.getElementById("admin-user-signature"),
  adminUserIsAdmin: () => document.getElementById("admin-user-is-admin"),



  // Scope of Work admin
  btnSaveScope: () => document.getElementById("btn-save-scope"),
  adminScopeRcc: () => document.getElementById("admin-scope-rcc"),
  adminScopeSteel: () => document.getElementById("admin-scope-steel"),
  adminScopeBoth: () => document.getElementById("admin-scope-both"),
  adminScopeNewRcc: () => document.getElementById("admin-scope-new-rcc"),
  adminScopeNewSteel: () => document.getElementById("admin-scope-new-steel"),
  adminScopeNewBoth: () => document.getElementById("admin-scope-new-both"),
  adminSupportRcc: () => document.getElementById("admin-support-rcc"),
  adminSupportSteel: () => document.getElementById("admin-support-steel"),
  adminSupportBoth: () => document.getElementById("admin-support-both"),
  adminSupportNewRcc: () => document.getElementById("admin-support-new-rcc"),
  adminSupportNewSteel: () => document.getElementById("admin-support-new-steel"),
  adminSupportNewBoth: () => document.getElementById("admin-support-new-both"),

  // Quotation Sections admin
  qsList: () => document.getElementById("qs-list"),
  btnSaveQSections: () => document.getElementById("btn-save-qsections"),
  btnAddQs: () => document.getElementById("btn-add-qs"),
  qsAddModal: () => document.getElementById("qs-add-modal"),
  qsNewHeading: () => document.getElementById("qs-new-heading"),
  qsInsertAfter: () => document.getElementById("qs-insert-after"),
  btnQsAddConfirm: () => document.getElementById("btn-qs-add-confirm"),
  btnQsAddCancel: () => document.getElementById("btn-qs-add-cancel"),

  // Studio building age
  dAge: () => document.getElementById("d-age"),

  toast: () => document.getElementById("toast"),
};

function fmtINR(v) {
  return "₹ " + Number(v || 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function escHtml(v) {
  return String(v ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

let _toastTimer = null;
function toast(msg, type = "info") {
  const t = el.toast();
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.classList.remove("hidden");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.add("hidden"), 3500);
}

// ── Enterprise Notification System ────────────────────────────────
function notify(title, text, type = "info", duration = 5000) {
  const center = document.getElementById("notification-center");
  if (!center) return;
  const item = document.createElement("div");
  item.className = `notification-item notify-${type}`;
  const icons = { success: "\u2705", error: "\u274C", warning: "\u26A0\uFE0F", info: "\u2139\uFE0F" };
  item.innerHTML = `
    <span class="notify-icon">${icons[type] || icons.info}</span>
    <div class="notify-body">
      <div class="notify-title">${escHtml(title)}</div>
      ${text ? `<div class="notify-text">${escHtml(text)}</div>` : ""}
    </div>
    <button class="notify-close" title="Dismiss">&times;</button>
  `;
  item.querySelector(".notify-close").addEventListener("click", () => dismissNotification(item));
  center.appendChild(item);
  if (duration > 0) {
    setTimeout(() => dismissNotification(item), duration);
  }
}

function dismissNotification(item) {
  if (!item || !item.parentNode) return;
  item.classList.add("removing");
  setTimeout(() => item.remove(), 300);
}

// ── Confirmation Modal ────────────────────────────────────────────
function confirmAction({ title = "Confirm Action", message = "Are you sure?", confirmText = "Confirm", cancelText = "Cancel", type = "warning" } = {}) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("confirm-modal");
    const titleEl = document.getElementById("confirm-modal-title");
    const msgEl = document.getElementById("confirm-modal-message");
    const confirmBtn = document.getElementById("confirm-modal-confirm");
    const cancelBtn = document.getElementById("confirm-modal-cancel");
    const iconEl = document.getElementById("confirm-modal-icon");
    if (!overlay) { resolve(false); return; }

    titleEl.textContent = title;
    msgEl.textContent = message;
    confirmBtn.textContent = confirmText;
    cancelBtn.textContent = cancelText;

    const icons = { warning: "\u26A0\uFE0F", danger: "\u{1F6A8}", info: "\u2139\uFE0F", success: "\u2705" };
    iconEl.className = `modal-icon modal-icon--${type}`;
    iconEl.textContent = icons[type] || icons.warning;

    if (type === "danger") {
      confirmBtn.className = "btn btn-pdf";
    } else {
      confirmBtn.className = "btn btn-primary";
    }

    overlay.classList.remove("hidden");
    confirmBtn.focus();

    function cleanup(result) {
      overlay.classList.add("hidden");
      confirmBtn.removeEventListener("click", onConfirm);
      cancelBtn.removeEventListener("click", onCancel);
      document.removeEventListener("keydown", onKey);
      resolve(result);
    }
    function onConfirm() { cleanup(true); }
    function onCancel() { cleanup(false); }
    function onKey(e) { if (e.key === "Escape") cleanup(false); }

    confirmBtn.addEventListener("click", onConfirm);
    cancelBtn.addEventListener("click", onCancel);
    document.addEventListener("keydown", onKey);
  });
}

// ── Last Refreshed Timestamp ──────────────────────────────────────
let _lastRefreshedAt = null;
function updateLastRefreshed() {
  _lastRefreshedAt = new Date();
  _renderLastRefreshed();
}
function _renderLastRefreshed() {
  const el = document.getElementById("last-refreshed");
  if (!el || !_lastRefreshedAt) return;
  const secs = Math.round((Date.now() - _lastRefreshedAt.getTime()) / 1000);
  if (secs < 5) el.textContent = "Just now";
  else if (secs < 60) el.textContent = `${secs}s ago`;
  else if (secs < 3600) el.textContent = `${Math.floor(secs / 60)}m ago`;
  else el.textContent = _lastRefreshedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
setInterval(_renderLastRefreshed, 10000);

// ── Animated Counter ──────────────────────────────────────────────
function animateCounter(element, targetValue) {
  if (!element) return;
  const current = parseInt(element.textContent) || 0;
  const target = parseInt(targetValue) || 0;
  if (current === target) { element.textContent = String(target); return; }
  const duration = 400;
  const start = performance.now();
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = String(Math.round(current + (target - current) * eased));
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Search Highlighting ───────────────────────────────────────────
function highlightText(text, query) {
  if (!query || !text) return escHtml(text);
  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return escHtml(text).replace(new RegExp(`(${escaped})`, "gi"), '<mark class="search-highlight">$1</mark>');
}

// ── Keyboard Shortcuts ────────────────────────────────────────────
function bindKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl+R  = Refresh (prevent browser reload)
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "r") {
      e.preventDefault();
      if (state.session?.authenticated) onRefresh();
      return;
    }
    // Escape = close profile menu or modal
    if (e.key === "Escape") {
      closeProfileMenu();
      return;
    }
    // Enter on login form
    if (e.key === "Enter" && !state.session?.authenticated) {
      const active = document.activeElement;
      if (active?.id === "login-email" || active?.id === "login-password") {
        e.preventDefault();
        onLogin();
      }
    }
    // Ctrl+1-5 for tab switching
    if ((e.ctrlKey || e.metaKey) && ["1","2","3","4","5"].includes(e.key)) {
      e.preventDefault();
      const tabs = ["overview", "enquiries", "studio", "pipeline", "deq", "admin"];
      const idx = parseInt(e.key) - 1;
      if (tabs[idx] && state.session?.authenticated) activateTab(tabs[idx]);
    }
  });
}

// ── Session Health Check ──────────────────────────────────────────
let _sessionCheckTimer = null;
function startSessionHealthCheck() {
  if (_sessionCheckTimer) clearInterval(_sessionCheckTimer);
  _sessionCheckTimer = setInterval(async () => {
    if (!state.session?.authenticated || document.hidden) return;
    try {
      const r = await fetch("/api/session", { credentials: "include", cache: "no-store" });
      if (!r.ok) throw new Error("Session check failed");
      const data = await r.json();
      if (!data.authenticated && state.session?.authenticated) {
        state.session.authenticated = false;
        updateAuthenticatedView();
        notify("Session Expired", "Your session has expired. Please sign in again.", "warning", 0);
      }
    } catch (_) { /* silent */ }
  }, SESSION_CHECK_INTERVAL_MS);
}

// ── System Status ─────────────────────────────────────────────────
async function checkSystemHealth() {
  try {
    const r = await fetch("/api/health", { cache: "no-store" });
    const dot = document.querySelector(".status-dot");
    const label = document.getElementById("system-status");
    if (r.ok) {
      if (dot) { dot.className = "status-dot status-dot--ok"; }
      if (label) { label.innerHTML = '<span class="status-dot status-dot--ok"></span> System Online'; }
    } else {
      throw new Error();
    }
  } catch (_) {
    const dot = document.querySelector(".status-dot");
    const label = document.getElementById("system-status");
    if (dot) { dot.className = "status-dot status-dot--error"; }
    if (label) { label.innerHTML = '<span class="status-dot status-dot--error"></span> Connection Issue'; }
  }
}

// ── Breadcrumb ────────────────────────────────────────────────────
function updateBreadcrumb(tab) {
  const bc = document.getElementById("breadcrumb");
  if (!bc) return;
  const names = { overview: "Home", enquiries: "New Enquiries", studio: "Quote Studio", pipeline: "BHC Pipeline", deq: "DEQ", admin: "Admin" };
  if (tab === "overview") {
    bc.innerHTML = "<span>Home</span>";
  } else {
    bc.innerHTML = `<span>Home</span><span>${names[tab] || tab}</span>`;
  }
}

function btnLoading(btn, loading) {
  if (!btn) return;
  if (loading) {
    btn.classList.add("loading");
    btn.disabled = true;
  } else {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

function setFeedback(msg, type = "info") {
  const box = el.detailFeedback();
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.className = `feedback ${type}`;
  box.classList.remove("hidden");
}

function setAdminFeedback(msg, type = "info") {
  const box = el.adminFeedback();
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.className = `feedback ${type}`;
  box.classList.remove("hidden");
}

function setAuthFeedback(msg, type = "info") {
  const box = el.authFeedback();
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.className = `feedback ${type}`;
  box.classList.remove("hidden");
}

function setAccountFeedback(msg, type = "info") {
  const box = el.accountFeedback();
  if (!msg) {
    box.classList.add("hidden");
    box.textContent = "";
    return;
  }
  box.textContent = msg;
  box.className = `feedback ${type}`;
  box.classList.remove("hidden");
}

function setPolicyState(policyNode, passed) {
  if (!policyNode) return;
  policyNode.classList.toggle("ok", !!passed);
}

function toggleProfilePasswordPanel(forceOpen) {
  const panel = el.profilePasswordPanel();
  const actions = el.profilePasswordActions();
  const trigger = el.btnOpenPasswordPanel();
  if (!panel || !actions || !trigger) return;

  const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : panel.classList.contains("hidden");
  panel.classList.toggle("hidden", !shouldOpen);
  actions.classList.toggle("hidden", !shouldOpen);
  trigger.textContent = shouldOpen ? "Hide Password Form" : "Change Password";

  if (!shouldOpen) {
    setAccountFeedback("");
  }
}

function closeProfileMenu() {
  const profileMenu = el.profileMenu();
  const profileButton = el.btnProfileMenu();
  toggleProfilePasswordPanel(false);
  if (profileMenu) {
    profileMenu.classList.add("hidden");
  }
  if (profileButton) {
    profileButton.setAttribute("aria-expanded", "false");
  }
}

function openProfileMenu() {
  const profileMenu = el.profileMenu();
  const profileButton = el.btnProfileMenu();
  if (profileMenu) {
    profileMenu.classList.remove("hidden");
  }
  if (profileButton) {
    profileButton.setAttribute("aria-expanded", "true");
  }
}

function toggleProfileMenu() {
  const profileMenu = el.profileMenu();
  if (!profileMenu) return;
  if (profileMenu.classList.contains("hidden")) {
    openProfileMenu();
  } else {
    closeProfileMenu();
  }
}

function bindProfileMenu() {
  const profileButton = el.btnProfileMenu();
  const profileMenu = el.profileMenu();
  if (!profileButton || !profileMenu) return;

  profileButton.addEventListener("click", (event) => {
    event.stopPropagation();
    if (!state.session?.authenticated) {
      return;
    }
    toggleProfileMenu();
  });

  profileMenu.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  document.addEventListener("click", () => {
    closeProfileMenu();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeProfileMenu();
    }
  });
}

function evaluateChangePassword() {
  const currentPassword = el.changeCurrentPassword().value;
  const newPassword = el.changeNewPassword().value;
  const confirmPassword = el.changeConfirmPassword().value;

  const checks = {
    length: newPassword.length >= 8,
    upper: /[A-Z]/.test(newPassword),
    lower: /[a-z]/.test(newPassword),
    digit: /\d/.test(newPassword),
    special: /[^A-Za-z0-9]/.test(newPassword),
    different: !!newPassword && newPassword !== currentPassword,
    match: !!newPassword && newPassword === confirmPassword,
  };

  setPolicyState(el.policyLength(), checks.length);
  setPolicyState(el.policyUpper(), checks.upper);
  setPolicyState(el.policyLower(), checks.lower);
  setPolicyState(el.policyDigit(), checks.digit);
  setPolicyState(el.policySpecial(), checks.special);
  setPolicyState(el.policyDifferent(), checks.different);
  setPolicyState(el.policyMatch(), checks.match);

  const coreScore = [checks.length, checks.upper, checks.lower, checks.digit, checks.special].filter(Boolean).length;
  const strengthEl = el.passwordStrength();
  if (!strengthEl) {
    return {
      valid: !!currentPassword && checks.length && checks.upper && checks.lower && checks.digit && checks.special && checks.different && checks.match,
      checks,
      currentPassword,
      newPassword,
      confirmPassword,
    };
  }
  if (coreScore <= 2) {
    strengthEl.textContent = "Password strength: Weak";
    strengthEl.className = "password-strength weak";
  } else if (coreScore <= 4) {
    strengthEl.textContent = "Password strength: Medium";
    strengthEl.className = "password-strength medium";
  } else {
    strengthEl.textContent = "Password strength: Strong";
    strengthEl.className = "password-strength strong";
  }

  const valid = !!currentPassword && checks.length && checks.upper && checks.lower && checks.digit && checks.special && checks.different && checks.match;
  el.btnChangePassword().disabled = !valid;

  return {
    valid,
    checks,
    currentPassword,
    newPassword,
    confirmPassword,
  };
}

function bindPasswordToggles() {
  el.passwordToggles().forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.target;
      const input = document.getElementById(targetId);
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      button.textContent = isPassword ? "Hide" : "Show";
    });
  });
}

function isMissingExcelError(err) {
  return String(err?.message || "").includes("No enquiry Excel file found");
}

function getDiscountPercentInput() {
  const raw = Number(el.discountPercent().value || 0);
  if (!Number.isFinite(raw)) return 0;
  if (raw < 0) return 0;
  if (raw > 100) return 100;
  return raw;
}

function extractDateKey(value) {
  const match = String(value || "").match(/^\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : "";
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function joinLines(values) {
  return Array.isArray(values) ? values.join("\n") : "";
}

function resetQuoteStudio() {
  state.selected = null;
  state.generatedQuote = null;
  setFeedback("");

  el.detailEmpty().classList.remove("hidden");
  el.detailPanel().classList.add("hidden");
  el.discountPercent().value = "";
}

async function loadExcelStatus() {
  const r = await api("/api/bhc/excel-status");
  const data = await r.json();
  state.excelStatus = data;
  const badge = el.excelSourceBadge();

  if (data.file_exists) {
    badge.textContent = "Connected";
    badge.classList.remove("missing");
    el.excelSourceName().textContent = data.file_name || "Workbook connected";
    el.excelSourcePath().textContent = data.file_path || "";
  } else {
    badge.textContent = "Not found";
    badge.classList.add("missing");
    el.excelSourceName().textContent = "Workbook not found";
    el.excelSourcePath().textContent = "Ensure the OneDrive file is synced and .env EXCEL_FILE_PATH is correct.";
  }
}

function openEmailDraft() {
  if (!state.selected || !state.generatedQuote) {
    toast("Generate a quote first", "error");
    return;
  }

  const body = {
    client_name: state.selected.name,
    to_email: state.selected.email || null,
    phone: state.selected.phone,
    property_type: state.selected.property_type,
    area: Number(state.selected.area_numeric || 0),
    building_system: state.selected.building_system || null,
    building_age: state.selected.building_age || null,
    timestamp: state.selected.timestamp || null,
    reference_number: state.generatedQuote?.reference_number || null,
    discount_percent: Number(state.generatedQuote?.pricing?.discount_percent || getDiscountPercentInput()),
  };

  fetch("/api/bhc/email-draft", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
    .then(async (r) => {
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || "Failed to generate email draft");
      }

      const blob = await r.blob();
      const cd = r.headers.get("Content-Disposition") || "";
      const match = cd.match(/filename="?([^";]+)"?/i);
      const filename = match ? match[1] : "BHC_Quotation_Draft.eml";

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast("Draft downloaded. Open it in Outlook to review/send.", "success");
      activateTab("pipeline");
      await Promise.all([loadProcessed(), loadDashboard()]);
    })
    .catch((err) => {
      toast(err.message, "error");
    });
}

async function api(url, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const maxAttempts = method === "GET" ? API_GET_RETRY_COUNT + 1 : 1;
  let lastError = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    try {
      const resp = await fetch(url, {
        credentials: "include",
        cache: "no-store",
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        const requestId = resp.headers.get("X-Request-ID") || err.request_id || "";
        const baseMessage = err.detail || `Request failed (${resp.status})`;
        const error = new Error(requestId ? `${baseMessage} [request_id: ${requestId}]` : baseMessage);

        if (attempt < maxAttempts && resp.status >= 500) {
          lastError = error;
          continue;
        }
        throw error;
      }

      return resp;
    } catch (err) {
      clearTimeout(timeoutId);
      const timeoutMessage = err?.name === "AbortError"
        ? `Request timed out after ${API_TIMEOUT_MS / 1000}s`
        : String(err?.message || "Network request failed");
      lastError = new Error(timeoutMessage);

      if (attempt >= maxAttempts) {
        throw lastError;
      }
    }
  }

  throw lastError || new Error("Request failed");
}

function activateTab(tabName) {
  state.activeTab = tabName;

  el.tabs().forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });

  el.tabPanels().forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tabName}`);
  });

  updateBreadcrumb(tabName);
  try { localStorage.setItem(TAB_STORAGE_KEY, tabName); } catch (_) {}

  if (tabName === "deq" && state.session?.authenticated) {
    const comingSoon = document.getElementById("deq-coming-soon");
    const tabBody = document.getElementById("deq-tab-body");
    if (comingSoon && tabBody) {
      if (DEQ_ENABLED) {
        comingSoon.classList.add("hidden");
        tabBody.classList.remove("hidden");
        loadDeqData();
      } else {
        comingSoon.classList.remove("hidden");
        tabBody.classList.add("hidden");
      }
    }
  }
}

function bindTabs() {
  el.tabs().forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.tab));
  });

  el.jumpTabButtons().forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.jumpTab;
      activateTab(target);
      if (target === "studio" && !state.selected) {
        toast("Select an enquiry first from New Enquiries", "info");
      }
    });
  });
}

function updateHeroStats() {
  animateCounter(el.heroPending(), state.pending.length);
  const quotedCount = state.processed.filter((row) => row.status === "Quoted" || row.status === "Converted").length;
  animateCounter(el.heroQuoted(), quotedCount);
  const convertedCount = state.processed.filter((row) => row.status === "Converted").length;
  const heroConverted = document.getElementById("hero-converted");
  if (heroConverted) animateCounter(heroConverted, convertedCount);
}

function updatePendingPropertyFilter() {
  const select = el.pendingPropertyFilter();
  const active = select.value;
  const unique = [...new Set(state.pending.map((x) => (x.property_type || "Unknown").trim()).filter(Boolean))].sort();

  select.innerHTML = '<option value="all">All Property Types</option>' +
    unique.map((property) => `<option value="${escHtml(property)}">${escHtml(property)}</option>`).join("");

  if (unique.includes(active)) {
    select.value = active;
  }
}

function applyPendingFilters() {
  const q = el.pendingSearch().value.trim().toLowerCase();
  const propertyType = el.pendingPropertyFilter().value;

  state.pendingFiltered = state.pending.filter((c) => {
    const matchesSearch = !q ||
      (c.name || "").toLowerCase().includes(q) ||
      (c.phone || "").toLowerCase().includes(q) ||
      (c.location || "").toLowerCase().includes(q);

    const matchesProperty = propertyType === "all" || (c.property_type || "") === propertyType;
    return matchesSearch && matchesProperty;
  });

  renderPending(state.pendingFiltered);
}

function applyProcessedFilters() {
  const q = el.processedSearch().value.trim().toLowerCase();
  const status = el.processedStatusFilter().value;
  const payment = el.processedPaymentFilter().value;
  const propertyType = el.processedPropertyFilter().value;
  const dateFrom = el.processedDateFrom().value;
  const dateTo = el.processedDateTo().value;

  state.processedFiltered = state.processed.filter((row) => {
    const matchesSearch = !q ||
      (row.client_name || "").toLowerCase().includes(q) ||
      (row.phone || "").toLowerCase().includes(q) ||
      String(row.enquiry_id || "").toLowerCase().includes(q);

    const matchesStatus = status === "all" || (row.status || "") === status;
    const matchesPayment = payment === "all" || String(row.payment_status || "") === payment;
    const matchesProperty = propertyType === "all" || String(row.property_type || "") === propertyType;
    const rowDate = extractDateKey(row.quote_generated_date);
    const matchesDateFrom = !dateFrom || (rowDate && rowDate >= dateFrom);
    const matchesDateTo = !dateTo || (rowDate && rowDate <= dateTo);
    return matchesSearch && matchesStatus && matchesPayment && matchesProperty && matchesDateFrom && matchesDateTo;
  });

  renderProcessed(state.processedFiltered);
}

function updateProcessedPropertyFilter() {
  const select = el.processedPropertyFilter();
  const active = select.value;
  const unique = [...new Set(state.processed.map((x) => (x.property_type || "Unknown").trim()).filter(Boolean))].sort();

  select.innerHTML = '<option value="all">All Property Types</option>' +
    unique.map((property) => `<option value="${escHtml(property)}">${escHtml(property)}</option>`).join("");

  select.value = unique.includes(active) ? active : "all";
}

function getSyncLabel(syncState) {
  if (syncState === "dirty") return "Unsaved";
  if (syncState === "saving") return "Saving";
  if (syncState === "error") return "Failed";
  return "Saved";
}

function setProcessedSync(enquiryId, syncState) {
  state.processedSync[String(enquiryId)] = syncState;
}

function getProcessedSync(enquiryId) {
  return state.processedSync[String(enquiryId)] || "saved";
}

function allowedPaymentsForStatus(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "converted") return ["Pending", "Paid"];
  if (normalized === "quoted") return ["Pending"];
  if (normalized === "dropped") return ["Pending"];
  return ["Pending"];
}

function getProcessedExportParams() {
  const params = new URLSearchParams();
  const search = el.processedSearch().value.trim();
  const status = el.processedStatusFilter().value;
  const paymentStatus = el.processedPaymentFilter().value;
  const propertyType = el.processedPropertyFilter().value;
  const dateFrom = el.processedDateFrom().value;
  const dateTo = el.processedDateTo().value;

  if (search) {
    params.set("search", search);
  }
  if (status && status !== "all") {
    params.set("status", status);
  }
  if (paymentStatus && paymentStatus !== "all") {
    params.set("payment_status", paymentStatus);
  }
  if (propertyType && propertyType !== "all") {
    params.set("property_type", propertyType);
  }
  if (dateFrom) {
    params.set("date_from", dateFrom);
  }
  if (dateTo) {
    params.set("date_to", dateTo);
  }

  return params;
}

function updateAuthenticatedView() {
  const authenticated = !!state.session?.authenticated;
  const isAdmin = !!state.session?.is_admin;
  const adminTabButton = el.adminTabButton();
  const profileButton = el.btnProfileMenu();

  el.authPanel().classList.toggle("hidden", authenticated);
  el.dashboardShell().classList.toggle("hidden", !authenticated);
  if (profileButton) {
    profileButton.classList.toggle("hidden", !authenticated);
  }
  closeProfileMenu();

  [el.btnRefresh(), el.btnExport()].forEach((button) => {
    button.disabled = !authenticated;
    button.classList.toggle("hidden", !authenticated);
  });

  if (adminTabButton) {
    adminTabButton.classList.toggle("hidden", !authenticated);
  }

  const avatarEl = document.getElementById("nav-avatar");
  const roleEl = document.getElementById("nav-role");

  if (!authenticated) {
    el.navUser().textContent = "Login required";
    el.forgotPasswordPanel().classList.add("hidden");
    if (avatarEl) avatarEl.textContent = "TR";
    if (roleEl) roleEl.classList.add("hidden");
    return;
  }

  const displayName = state.session?.full_name || state.session?.email || "Signed in";
  el.navUser().textContent = displayName;
  el.accountEmail().textContent = state.session?.email || "";

  if (avatarEl) {
    const initials = displayName.trim().split(/\s+/).filter(Boolean).map((w) => w[0].toUpperCase()).join("").slice(0, 2) || "?";
    avatarEl.textContent = initials;
  }
  if (roleEl) {
    roleEl.textContent = isAdmin ? "Administrator" : "Team Member";
    roleEl.classList.remove("hidden");
  }

  // Populate profile fields
  const profileDesig = el.profileDesignation();
  if (profileDesig) profileDesig.value = state.session?.designation || "";
  const sigStatus = el.profileSignatureStatus();
  if (sigStatus) sigStatus.textContent = state.session?.has_signature ? "✓ Uploaded" : "Not uploaded";
  const sqStatus = el.profileSqStatus();
  if (sqStatus) sqStatus.textContent = state.session?.has_security_question ? "(Set ✓)" : "(Not set)";
}

function toggleForgotPasswordPanel(forceOpen) {
  const panel = el.forgotPasswordPanel();
  const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : panel.classList.contains("hidden");
  panel.classList.toggle("hidden", !shouldOpen);
  // Reset to step 1 whenever opening
  if (shouldOpen) {
    el.forgotStepEmail().classList.remove("hidden");
    el.forgotStepAnswer().classList.add("hidden");
    el.forgotEmail().value = "";
    el.forgotAnswer().value = "";
    el.forgotNewPassword().value = "";
    el.forgotConfirmPassword().value = "";
  }
}

function updateAdminView() {
  const isAdmin = !!state.session?.is_admin;

  el.adminLoginCard().classList.toggle("hidden", isAdmin);
  el.adminConfigCard().classList.toggle("hidden", !isAdmin);

  if (!isAdmin) {
    el.adminLoginHelp().textContent = "Only the admin user can edit settings. You can view this tab but changes require admin access.";
  }

  updateAdminEditVisibility();
  if (isAdmin) lockAllAdminSections();
}

function _renderSlabTable(body, slabs, dataPrefix) {
  if (!slabs.length) {
    body.innerHTML = `<tr><td colspan="5" class="muted">No pricing slabs configured.</td></tr>`;
    return;
  }

  body.innerHTML = slabs.map((slab, index) => `
    <tr class="${slab._new ? 'slab-row-new' : ''}">
      <td><input type="number" min="0" step="1" placeholder="e.g. 0" data-${dataPrefix}-field="min_area" data-${dataPrefix}-index="${index}" value="${Number(slab.min_area || 0)}" /></td>
      <td><input type="number" min="0" step="1" placeholder="e.g. 2000" data-${dataPrefix}-field="max_area" data-${dataPrefix}-index="${index}" value="${Number(slab.max_area || 0)}" /></td>
      <td><input type="text" placeholder="Label (required)" data-${dataPrefix}-field="label" data-${dataPrefix}-index="${index}" value="${escHtml(slab.label || "")}" class="${!slab.label ? 'slab-input-required' : ''}" /></td>
      <td><input type="number" min="0" step="0.01" placeholder="e.g. 10000" data-${dataPrefix}-field="quoted_price" data-${dataPrefix}-index="${index}" value="${Number(slab.quoted_price || 0)}" /></td>
      <td><button class="btn btn-sm btn-outline" data-delete-${dataPrefix}-index="${index}">Delete</button></td>
    </tr>
  `).join("");

  body.querySelectorAll(`input[data-${dataPrefix}-index]`).forEach((input) => {
    input.addEventListener("input", () => {
      const index = Number(input.dataset[`${dataPrefix}Index`]);
      const field = input.dataset[`${dataPrefix}Field`];
      if (!slabs[index]) return;
      slabs[index][field] = field === "label" ? input.value : Number(input.value || 0);
      // Update required highlight on label field
      if (field === "label") {
        input.classList.toggle("slab-input-required", !input.value.trim());
      }
    });
  });

  body.querySelectorAll(`button[data-delete-${dataPrefix}-index]`).forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset[`delete${dataPrefix.charAt(0).toUpperCase() + dataPrefix.slice(1)}Index`]);
      slabs.splice(index, 1);
      _renderSlabTable(body, slabs, dataPrefix);
    });
  });
}

function renderAdminPricingRows() {
  const slabs = state.adminConfig?.pricing?.slabs || [];
  _renderSlabTable(el.adminPricingBody(), slabs, "pricing");

  const newSlabs = state.adminConfig?.pricing?.new_building_slabs || [];
  _renderSlabTable(el.adminNewBuildingPricingBody(), newSlabs, "nbpricing");
}

function populateAdminForm() {
  if (!state.adminConfig) {
    return;
  }

  const company = state.adminConfig.company || {};
  const documentConfig = state.adminConfig.document || {};

  el.adminDbPath().textContent = state.adminConfig.db_path || "";

  el.adminCompanyName().value = company.company_name || "";
  el.adminCompanySubtitle().value = company.company_subtitle || "";
  el.adminCompanyAddress().value = company.company_address || "";
  el.adminCompanyPhone().value = company.company_phone || "";
  el.adminCompanyEmail().value = company.company_email || "";
  el.adminContactName().value = company.contact_name || "";
  document.getElementById("admin-urgency-surcharge").value = (company.urgency_surcharge_percent != null && company.urgency_surcharge_percent !== "") ? company.urgency_surcharge_percent : "10";
  document.getElementById("admin-gst-percent").value = company.gst_percent || "18";

  el.adminCompanyProfile().value = joinLines(documentConfig.company_profile_paragraphs);
  el.adminTuvHistory().value = joinLines(documentConfig.tuv_history_paragraphs);
  el.adminServiceCapabilities().value = joinLines(documentConfig.service_capabilities);
  el.adminDeliverables().value = joinLines(documentConfig.deliverables);
  el.adminPaymentTerms().value = joinLines(documentConfig.payment_terms);
  el.adminOtherTerms().value = joinLines(documentConfig.other_terms);
  el.adminSystemNote().value = documentConfig.system_generated_note || "";

  renderAdminPricingRows();
  renderAdminUsers();
  populateAdminScopeFields();
  renderQSSectionsList();
  lockAllAdminSections();
  updateAdminEditVisibility();
}

/* ── Audit Log ────────────────────────────────────────── */
let _auditData = null;

async function loadAuditLogs() {
  try {
    el.btnLoadAudit().disabled = true;
    el.btnLoadAudit().textContent = "Loading…";
    const r = await api("/api/bhc/admin/audit-events?limit=500");
    _auditData = await r.json();
    renderAuditLogs();
    toast("Audit logs loaded", "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    el.btnLoadAudit().disabled = false;
    el.btnLoadAudit().textContent = "Load Logs";
  }
}

function renderAuditLogs() {
  if (!_auditData) return;
  const filter = el.auditFilterType().value;
  const ROUTINE = new Set(["AUTH_LOGIN_SUCCESS","AUTH_LOGIN_FAILED","AUTH_LOGOUT","AUTH_PASSWORD_CHANGED"]);
  let events = [];
  (_auditData.security_events || []).forEach(e => events.push({ ...e, _source: "security" }));
  (_auditData.workflow_events || []).forEach(e => events.push({ ...e, _source: "workflow" }));
  if (filter === "important") {
    events = events.filter(e => !ROUTINE.has(e.event_type));
  }
  events.sort((a, b) => b.id - a.id || b.event_time.localeCompare(a.event_time));

  const body = el.auditLogBody();
  if (!events.length) {
    body.innerHTML = '<tr><td colspan="6" class="muted">No events found.</td></tr>';
    el.auditLogWrap().classList.remove("hidden");
    el.auditLogEmpty().classList.add("hidden");
    el.auditLogCount().classList.add("hidden");
    return;
  }

  body.innerHTML = events.map(e => {
    const time = e.event_time ? e.event_time.replace("T", " ").slice(0, 19) : "—";
    const sevClass = (e.severity || "INFO").toLowerCase();
    const meta = e.metadata || e.enquiry_id ? formatAuditMeta(e) : "";
    const target = e.target || e.enquiry_id || "—";
    return `<tr>
      <td>${escHtml(time)}</td>
      <td><span class="audit-type">${escHtml(e.event_type)}</span></td>
      <td><span class="audit-sev audit-sev--${sevClass}">${escHtml(e.severity)}</span></td>
      <td>${escHtml(e.actor_email)}</td>
      <td>${escHtml(target)}</td>
      <td>${meta}</td>
    </tr>`;
  }).join("");

  el.auditLogWrap().classList.remove("hidden");
  el.auditLogEmpty().classList.add("hidden");
  el.auditLogCount().classList.remove("hidden");
  el.auditLogCount().textContent = `Showing ${events.length} event${events.length !== 1 ? "s" : ""}`;
}

function formatAuditMeta(e) {
  const parts = [];
  const m = e.metadata || {};
  if (e.enquiry_id) parts.push(`Enquiry: ${e.enquiry_id}`);
  for (const [k, v] of Object.entries(m)) {
    if (k === "raw") { parts.push(String(v)); continue; }
    parts.push(`${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`);
  }
  return parts.length ? escHtml(parts.join(", ")) : "";
}

async function loadSession() {
  const r = await api("/api/session");
  state.session = await r.json();
  updateAuthenticatedView();
  updateAdminView();
}

async function loadAdminConfig() {
  if (!state.session?.authenticated || !state.session?.is_admin) {
    state.adminConfig = null;
    updateAdminView();
    return;
  }

  const r = await api("/api/bhc/admin/config");
  state.adminConfig = await r.json();
  populateAdminForm();
  updateAdminView();
}

function renderAdminUsers() {
  const body = el.adminUsersBody();
  const users = state.adminConfig?.users || [];

  if (!users.length) {
    body.innerHTML = '<tr><td colspan="8" class="muted">No users found.</td></tr>';
    return;
  }

  body.innerHTML = users.map((user, index) => `
    <tr>
      <td>${escHtml(user.email)}</td>
      <td>${escHtml(user.full_name)}</td>
      <td>${escHtml(user.designation || "—")}</td>
      <td>${user.has_signature ? '<span class="sync-pill saved">Uploaded</span>' : `<label class="btn btn-sm btn-outline" style="cursor:pointer"><input type="file" accept=".png,.jpg,.jpeg" data-sig-upload="${index}" hidden />Upload</label>`}</td>
      <td>${user.is_admin ? '<span class="sync-pill saving">Admin</span>' : '<span class="sync-pill saved">User</span>'}</td>
      <td>${user.is_active ? '<span class="sync-pill saved">Active</span>' : '<span class="sync-pill dirty">Pending</span>'}</td>
      <td>${user.must_change_password ? '<span class="sync-pill dirty">Must change</span>' : '<span class="sync-pill saved">OK</span>'}</td>
      <td>
        <div class="inline-reset-row">
          ${!user.is_active ? `<button class="btn btn-sm btn-primary" data-user-approve="${index}">Approve</button>` : ''}
          <input type="password" data-user-reset-index="${index}" class="search-input" placeholder="Temp password" style="max-width:130px" />
          <button class="btn btn-sm btn-outline" data-user-reset-button="${index}">Reset</button>
        </div>
      </td>
    </tr>
  `).join("");

  body.querySelectorAll("input[data-sig-upload]").forEach((input) => {
    input.addEventListener("change", async () => {
      const index = Number(input.dataset.sigUpload);
      const user = users[index];
      const file = input.files?.[0];
      if (!file) return;
      const form = new FormData();
      form.append("file", file);
      try {
        await fetch(`/api/bhc/user/signature`, {
          method: "POST",
          credentials: "include",
          body: form,
        }).then(async (r) => {
          if (!r.ok) { const d = await r.json().catch(() => ({})); throw new Error(d.detail || "Upload failed"); }
        });
        await loadAdminConfig();
        toast(`Signature uploaded for ${user.email}`, "success");
      } catch (err) {
        toast(err.message, "error");
      }
    });
  });

  body.querySelectorAll("button[data-user-approve]").forEach((button) => {
    button.addEventListener("click", async () => {
      const index = Number(button.dataset.userApprove);
      const user = users[index];
      try {
        await api("/api/bhc/admin/users/approve", {
          method: "POST",
          body: JSON.stringify({ email: user.email }),
        });
        await loadAdminConfig();
        setAdminFeedback(`User ${user.email} approved.`, "success");
        toast(`${user.email} approved`, "success");
      } catch (err) {
        setAdminFeedback(err.message, "error");
        toast(err.message, "error");
      }
    });
  });

  body.querySelectorAll("button[data-user-reset-button]").forEach((button) => {
    button.addEventListener("click", async () => {
      const index = Number(button.dataset.userResetButton);
      const user = users[index];
      const passwordInput = body.querySelector(`input[data-user-reset-index="${index}"]`);
      const newPassword = passwordInput?.value || "";
      if (!newPassword) {
        setAdminFeedback("Enter a temporary password before resetting.", "error");
        return;
      }

      try {
        await api("/api/bhc/admin/users/reset-password", {
          method: "POST",
          body: JSON.stringify({ email: user.email, new_password: newPassword }),
        });
        passwordInput.value = "";
        await loadAdminConfig();
        setAdminFeedback(`Password reset for ${user.email}.`, "success");
        toast(`Password reset for ${user.email}`, "success");
      } catch (err) {
        setAdminFeedback(err.message, "error");
        toast(err.message, "error");
      }
    });
  });
}

// ── Scope of Work admin ────────────────────────────────────────────

function populateAdminScopeFields() {
  const scopeData = state.adminConfig?.scope_of_work || {};
  const supportData = state.adminConfig?.support_documents || {};

  el.adminScopeRcc().value = joinLines(scopeData.rcc || []);
  el.adminScopeSteel().value = joinLines(scopeData.steel || []);
  el.adminScopeBoth().value = joinLines(scopeData.both || []);
  el.adminScopeNewRcc().value = joinLines(scopeData.new_rcc || []);
  el.adminScopeNewSteel().value = joinLines(scopeData.new_steel || []);
  el.adminScopeNewBoth().value = joinLines(scopeData.new_both || []);
  el.adminSupportRcc().value = joinLines(supportData.rcc || []);
  el.adminSupportSteel().value = joinLines(supportData.steel || []);
  el.adminSupportBoth().value = joinLines(supportData.both || []);
  el.adminSupportNewRcc().value = joinLines(supportData.new_rcc || []);
  el.adminSupportNewSteel().value = joinLines(supportData.new_steel || []);
  el.adminSupportNewBoth().value = joinLines(supportData.new_both || []);
}

async function onSaveScope() {
  try {
    setAdminFeedback("Saving scope of work and support documents...", "info");

    const scopePayload = {
      rcc: splitLines(el.adminScopeRcc().value),
      steel: splitLines(el.adminScopeSteel().value),
      both: splitLines(el.adminScopeBoth().value),
      new_rcc: splitLines(el.adminScopeNewRcc().value),
      new_steel: splitLines(el.adminScopeNewSteel().value),
      new_both: splitLines(el.adminScopeNewBoth().value),
    };
    const supportPayload = {
      rcc: splitLines(el.adminSupportRcc().value),
      steel: splitLines(el.adminSupportSteel().value),
      both: splitLines(el.adminSupportBoth().value),
      new_rcc: splitLines(el.adminSupportNewRcc().value),
      new_steel: splitLines(el.adminSupportNewSteel().value),
      new_both: splitLines(el.adminSupportNewBoth().value),
    };

    const [scopeRes, supportRes] = await Promise.all([
      api("/api/bhc/admin/scope-of-work", { method: "PUT", body: JSON.stringify(scopePayload) }),
      api("/api/bhc/admin/support-documents", { method: "PUT", body: JSON.stringify(supportPayload) }),
    ]);

    const scopeResult = await scopeRes.json();
    const supportResult = await supportRes.json();

    state.adminConfig.scope_of_work = scopeResult.scope_of_work || {};
    state.adminConfig.support_documents = supportResult.support_documents || {};
    populateAdminScopeFields();
    setAdminFeedback("Scope of work and support documents saved.", "success");
    toast("Scope of work saved", "success");
    lockAdminSection("scope");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

// ── Quotation Sections admin ────────────────────────────────────────

let _qsDragSrcId = null;
let _qsEditingId = null;
let _qsLocalSections = [];

function renderQSSectionsList() {
  const sections = state.adminConfig?.quotation_sections || [];
  _qsLocalSections = JSON.parse(JSON.stringify(sections));
  _renderQSItems();
}

function _renderQSItems() {
  const container = el.qsList();
  if (!container) return;
  const isLocked = container.closest("[data-admin-section]")?.classList.contains("admin-locked");

  container.innerHTML = _qsLocalSections.map((sec, idx) => {
    const typeLabel = { list: "Numbered List", paragraph: "Paragraphs", table: "Table", dynamic: "Dynamic" }[sec.content_type] || sec.content_type;
    const systemBadge = sec.is_system ? '<span class="qs-badge qs-badge--system">System</span>' : '<span class="qs-badge qs-badge--custom">Custom</span>';
    const hiddenBadge = !sec.is_visible ? '<span class="qs-badge qs-badge--hidden">Hidden</span>' : '';
    const isDynamic = sec.content_type === "dynamic";

    return `
      <div class="qs-item" data-qs-id="${sec.id}" data-qs-idx="${idx}" draggable="${!isLocked}">
        <div class="qs-drag-handle" title="Drag to reorder">&#9776;</div>
        <div class="qs-item-info">
          <div class="qs-item-heading">${escHtml(sec.heading)}</div>
          <div class="qs-item-meta">${systemBadge}${hiddenBadge} ${escHtml(typeLabel)} &middot; Order: ${sec.sort_order}</div>
        </div>
        <label class="qs-toggle" title="${sec.is_visible ? 'Visible — click to hide' : 'Hidden — click to show'}">
          <input type="checkbox" ${sec.is_visible ? 'checked' : ''} data-qs-toggle="${sec.id}" />
          <span class="qs-toggle-slider"></span>
        </label>
        <div class="qs-item-actions">
          ${!isDynamic ? `<button class="btn btn-outline btn-sm" data-qs-edit="${sec.id}">Edit</button>` : ''}
          ${!sec.is_system ? `<button class="btn btn-outline btn-sm" style="color:#dc2626" data-qs-delete="${sec.id}">Delete</button>` : ''}
        </div>
      </div>
      <div id="qs-edit-panel-${sec.id}" class="qs-edit-panel hidden"></div>
    `;
  }).join("");

  // Bind drag events
  container.querySelectorAll(".qs-item[draggable='true']").forEach(item => {
    item.addEventListener("dragstart", _onQsDragStart);
    item.addEventListener("dragover", _onQsDragOver);
    item.addEventListener("dragleave", _onQsDragLeave);
    item.addEventListener("drop", _onQsDrop);
    item.addEventListener("dragend", _onQsDragEnd);
  });

  // Bind toggle events
  container.querySelectorAll("[data-qs-toggle]").forEach(toggle => {
    toggle.addEventListener("change", _onQsToggle);
  });

  // Bind edit events
  container.querySelectorAll("[data-qs-edit]").forEach(btn => {
    btn.addEventListener("click", () => _openQsEdit(Number(btn.dataset.qsEdit)));
  });

  // Bind delete events
  container.querySelectorAll("[data-qs-delete]").forEach(btn => {
    btn.addEventListener("click", () => _onQsDelete(Number(btn.dataset.qsDelete)));
  });
}

function _onQsDragStart(e) {
  _qsDragSrcId = Number(e.currentTarget.dataset.qsId);
  e.currentTarget.classList.add("qs-dragging");
  e.dataTransfer.effectAllowed = "move";
}

function _onQsDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  e.currentTarget.classList.add("qs-drag-over");
}

function _onQsDragLeave(e) {
  e.currentTarget.classList.remove("qs-drag-over");
}

function _onQsDrop(e) {
  e.preventDefault();
  e.currentTarget.classList.remove("qs-drag-over");
  const targetId = Number(e.currentTarget.dataset.qsId);
  if (_qsDragSrcId === null || _qsDragSrcId === targetId) return;

  const srcIdx = _qsLocalSections.findIndex(s => s.id === _qsDragSrcId);
  const tgtIdx = _qsLocalSections.findIndex(s => s.id === targetId);
  if (srcIdx < 0 || tgtIdx < 0) return;

  const [moved] = _qsLocalSections.splice(srcIdx, 1);
  _qsLocalSections.splice(tgtIdx, 0, moved);
  _qsLocalSections.forEach((s, i) => s.sort_order = (i + 1) * 10);
  _renderQSItems();
}

function _onQsDragEnd(e) {
  e.currentTarget.classList.remove("qs-dragging");
  _qsDragSrcId = null;
}

async function _onQsToggle(e) {
  const secId = Number(e.target.dataset.qsToggle);
  const visible = e.target.checked;
  try {
    const r = await api(`/api/bhc/admin/quotation-sections/${secId}`, {
      method: "PUT",
      body: JSON.stringify({ is_visible: visible }),
    });
    const data = await r.json();
    // Update local
    const idx = _qsLocalSections.findIndex(s => s.id === secId);
    if (idx >= 0) _qsLocalSections[idx] = data.section;
    _renderQSItems();
    toast(`Section ${visible ? 'shown' : 'hidden'}`, "success");
  } catch (err) {
    toast(err.message, "error");
    e.target.checked = !visible; // revert
  }
}

function _openQsEdit(secId) {
  const sec = _qsLocalSections.find(s => s.id === secId);
  if (!sec) return;
  // Close any other open panel
  document.querySelectorAll(".qs-edit-panel").forEach(p => p.classList.add("hidden"));

  const panel = document.getElementById(`qs-edit-panel-${secId}`);
  if (!panel) return;

  // For table sections, extract _col_headers and strip from displayed content
  let displayContent = sec.content || [];
  let colHeaders = ["Task / Activity", "Duration"];
  if (sec.content_type === "table" && displayContent.length && displayContent[0]?._col_headers) {
    const hdr = displayContent[0];
    colHeaders = Array.isArray(hdr.headers) ? hdr.headers : [hdr.col1 || "Task / Activity", hdr.col2 || "Duration"];
    displayContent = displayContent.slice(1);
  }

  const contentLines = displayContent.map(item => {
    if (typeof item === "object") return JSON.stringify(item);
    return String(item);
  }).join("\n");

  const colNameRow = sec.content_type === "table" ? `
    <div class="qs-tbl-edit-cols">
      ${colHeaders.map((h, i) => `
        <label style="flex:${i === 0 ? 2 : 1}">
          <span style="font-size:11px;color:var(--slate-500)">Column ${i + 1} Name</span>
          <input class="search-input qs-edit-col-name" data-col-idx="${i}" value="${escHtml(h)}" placeholder="Column ${i + 1} name" />
        </label>
      `).join("")}
    </div>` : "";

  panel.innerHTML = `
    <label><span>Heading</span>
      <input id="qs-edit-heading-${secId}" class="search-input" value="${escHtml(sec.heading)}" />
    </label>
    ${colNameRow}
    <label><span>Content (one item per line${sec.content_type === 'table' ? ', JSON objects' : ''})</span>
      <textarea id="qs-edit-content-${secId}" class="search-input admin-textarea" rows="6">${escHtml(contentLines)}</textarea>
    </label>
    <div class="qs-edit-actions">
      <button class="btn btn-primary btn-sm" id="qs-edit-save-${secId}">Save</button>
      <button class="btn btn-outline btn-sm" id="qs-edit-cancel-${secId}">Cancel</button>
    </div>
  `;
  panel.classList.remove("hidden");

  document.getElementById(`qs-edit-save-${secId}`).addEventListener("click", () => _saveQsEdit(secId));
  document.getElementById(`qs-edit-cancel-${secId}`).addEventListener("click", () => panel.classList.add("hidden"));
}

async function _saveQsEdit(secId) {
  const sec = _qsLocalSections.find(s => s.id === secId);
  if (!sec) return;

  const heading = document.getElementById(`qs-edit-heading-${secId}`)?.value.trim();
  const rawContent = document.getElementById(`qs-edit-content-${secId}`)?.value || "";

  let content;
  if (sec.content_type === "table") {
    // Each line should be a JSON object; strip any existing _col_headers line
    const rows = rawContent.split("\n").filter(l => l.trim()).map(l => {
      try { return JSON.parse(l); } catch { return { text: l.trim() }; }
    }).filter(r => !r._col_headers);
    // Re-attach updated column headers from the edit panel inputs
    const colInputs = Array.from(panel.querySelectorAll(".qs-edit-col-name"));
    const headers = colInputs.length
      ? colInputs.map((inp, i) => inp.value.trim() || `Column ${i + 1}`)
      : ["Task / Activity", "Duration"];
    content = [{ _col_headers: true, headers }, ...rows];
  } else {
    content = rawContent.split("\n").map(l => l.trim()).filter(l => l);
  }

  try {
    const r = await api(`/api/bhc/admin/quotation-sections/${secId}`, {
      method: "PUT",
      body: JSON.stringify({ heading, content }),
    });
    const data = await r.json();
    const idx = _qsLocalSections.findIndex(s => s.id === secId);
    if (idx >= 0) _qsLocalSections[idx] = data.section;
    _renderQSItems();
    toast("Section updated", "success");
  } catch (err) {
    toast(err.message, "error");
  }
}

async function _onQsDelete(secId) {
  if (!confirm("Delete this custom section? This cannot be undone.")) return;
  try {
    await api(`/api/bhc/admin/quotation-sections/${secId}`, { method: "DELETE" });
    _qsLocalSections = _qsLocalSections.filter(s => s.id !== secId);
    _renderQSItems();
    toast("Section deleted", "success");
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ── Add Section Modal — interactive builder ── */
let _qsActiveType = "list";
let _qsTableColumns = ["Task / Activity", "Duration"];

function _qsRenderTableHeader() {
  const header = document.getElementById("qs-tbl-header");
  if (!header) return;
  header.innerHTML = _qsTableColumns.map((col, i) => `
    <div class="qs-tbl-col-wrap" style="flex:${i === 0 ? 2 : 1}">
      <input class="qs-tbl-col-input" data-col-index="${i}" value="${escHtml(col)}" placeholder="Column ${i + 1} name" title="Edit column name" />
      ${_qsTableColumns.length > 1
        ? `<button type="button" class="qs-tbl-col-remove" data-remove-col="${i}" title="Remove column">&times;</button>`
        : ""}
    </div>
  `).join("") +
  `<button type="button" class="btn btn-outline btn-sm qs-tbl-add-col" id="btn-qs-add-col">+ Col</button>` +
  `<span style="width:32px;flex-shrink:0"></span>`;

  header.querySelectorAll(".qs-tbl-col-input").forEach(inp => {
    inp.addEventListener("input", () => {
      const idx = Number(inp.dataset.colIndex);
      _qsTableColumns[idx] = inp.value;
      document.querySelectorAll("#qs-table-rows .qs-table-row").forEach(row => {
        const cell = row.querySelectorAll("input.qs-tbl-cell")[idx];
        if (cell) cell.placeholder = inp.value || `Column ${idx + 1}`;
      });
    });
  });
  header.querySelectorAll(".qs-tbl-col-remove").forEach(btn => {
    btn.addEventListener("click", () => _qsRemoveTableColumn(Number(btn.dataset.removeCol)));
  });
  document.getElementById("btn-qs-add-col")?.addEventListener("click", _qsAddTableColumn);
}

function _qsAddTableColumn() {
  _qsTableColumns.push(`Column ${_qsTableColumns.length + 1}`);
  _qsRenderTableHeader();
  // Append a new cell to every existing row
  document.querySelectorAll("#qs-table-rows .qs-table-row").forEach(row => {
    _qsAppendCellToRow(row, _qsTableColumns.length - 1);
  });
  // Focus the new header input
  const newInput = document.getElementById("qs-tbl-header")?.querySelectorAll(".qs-tbl-col-input");
  if (newInput?.length) newInput[newInput.length - 1].focus();
}

function _qsRemoveTableColumn(colIdx) {
  if (_qsTableColumns.length <= 1) return;
  _qsTableColumns.splice(colIdx, 1);
  _qsRenderTableHeader();
  document.querySelectorAll("#qs-table-rows .qs-table-row").forEach(row => {
    const cells = row.querySelectorAll("input.qs-tbl-cell");
    cells[colIdx]?.remove();
    // Re-index and re-style remaining cells
    row.querySelectorAll("input.qs-tbl-cell").forEach((cell, i) => {
      cell.dataset.cellIndex = i;
      cell.style.flex = i === 0 ? "2" : "1";
      cell.placeholder = _qsTableColumns[i] || `Column ${i + 1}`;
    });
  });
}

function _qsAppendCellToRow(rowEl, colIdx) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "qs-tbl-cell";
  input.dataset.cellIndex = colIdx;
  input.placeholder = _qsTableColumns[colIdx] || `Column ${colIdx + 1}`;
  input.style.flex = colIdx === 0 ? "2" : "1";
  const removeBtn = rowEl.querySelector(".qs-builder-remove");
  rowEl.insertBefore(input, removeBtn);
}

function _openQsAddModal() {
  const modal = el.qsAddModal();
  // Reset fields
  el.qsNewHeading().value = "";
  _qsActiveType = "list";
  _qsSetActiveType("list");
  _qsResetBuilders();
  _qsAddBuilderItem("list");  // start with one empty item

  // Populate "Insert After" dropdown
  const sel = el.qsInsertAfter();
  sel.innerHTML = '<option value="end">— End of quotation (last section) —</option>';
  _qsLocalSections.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.heading;
    sel.appendChild(opt);
  });

  modal.classList.remove("hidden");
  setTimeout(() => el.qsNewHeading().focus(), 100);
}

function _qsCloseModal() {
  el.qsAddModal().classList.add("hidden");
}

function _qsSetActiveType(type) {
  _qsActiveType = type;
  document.querySelectorAll(".qs-type-card").forEach(card => {
    const isMatch = card.dataset.typeValue === type;
    card.classList.toggle("qs-type-card--active", isMatch);
    card.querySelector("input[type=radio]").checked = isMatch;
  });
  // Show matching builder, hide others
  document.getElementById("qs-builder-list").classList.toggle("hidden", type !== "list");
  document.getElementById("qs-builder-paragraph").classList.toggle("hidden", type !== "paragraph");
  document.getElementById("qs-builder-table").classList.toggle("hidden", type !== "table");
  // If switching to a builder that's empty, add one starter item
  const containerId = type === "list" ? "qs-list-items" : type === "paragraph" ? "qs-para-items" : "qs-table-rows";
  if (!document.getElementById(containerId).children.length) {
    _qsAddBuilderItem(type);
  }
}

function _qsResetBuilders() {
  document.getElementById("qs-list-items").innerHTML = "";
  document.getElementById("qs-para-items").innerHTML = "";
  document.getElementById("qs-table-rows").innerHTML = "";
  // Reset columns to defaults and re-render header
  _qsTableColumns = ["Task / Activity", "Duration"];
  _qsRenderTableHeader();
}

function _qsAddBuilderItem(type, value, value2) {
  if (type === "list") {
    const container = document.getElementById("qs-list-items");
    const idx = container.children.length + 1;
    const div = document.createElement("div");
    div.className = "qs-builder-item";
    div.innerHTML = `
      <span class="qs-builder-item-num">${idx}</span>
      <input type="text" placeholder="Enter list item..." value="${escHtml(value || "")}" />
      <button type="button" class="qs-builder-remove" title="Remove">&times;</button>`;
    div.querySelector(".qs-builder-remove").addEventListener("click", () => { div.remove(); _qsRenumberItems(); });
    container.appendChild(div);
    if (!value) div.querySelector("input").focus();
  } else if (type === "paragraph") {
    const container = document.getElementById("qs-para-items");
    const div = document.createElement("div");
    div.className = "qs-builder-item";
    div.innerHTML = `
      <textarea placeholder="Enter paragraph text...">${escHtml(value || "")}</textarea>
      <button type="button" class="qs-builder-remove" title="Remove">&times;</button>`;
    div.querySelector(".qs-builder-remove").addEventListener("click", () => div.remove());
    container.appendChild(div);
    if (!value) div.querySelector("textarea").focus();
  } else if (type === "table") {
    const container = document.getElementById("qs-table-rows");
    const div = document.createElement("div");
    div.className = "qs-builder-item qs-table-row";
    const cellsHtml = _qsTableColumns.map((col, i) =>
      `<input type="text" class="qs-tbl-cell" data-cell-index="${i}" style="flex:${i === 0 ? 2 : 1}" placeholder="${escHtml(col)}" value="${escHtml(i === 0 ? (value || "") : (i === 1 ? (value2 || "") : ""))}" />`
    ).join("");
    div.innerHTML = cellsHtml + `<button type="button" class="qs-builder-remove" title="Remove">&times;</button>`;
    div.querySelector(".qs-builder-remove").addEventListener("click", () => div.remove());
    container.appendChild(div);
    if (!value) div.querySelector("input").focus();
  }
}

function _qsRenumberItems() {
  document.querySelectorAll("#qs-list-items .qs-builder-item").forEach((item, i) => {
    const num = item.querySelector(".qs-builder-item-num");
    if (num) num.textContent = i + 1;
  });
}

function _qsCollectContent() {
  if (_qsActiveType === "list") {
    return Array.from(document.querySelectorAll("#qs-list-items .qs-builder-item input"))
      .map(inp => inp.value.trim()).filter(v => v);
  } else if (_qsActiveType === "paragraph") {
    return Array.from(document.querySelectorAll("#qs-para-items .qs-builder-item textarea"))
      .map(ta => ta.value.trim()).filter(v => v);
  } else if (_qsActiveType === "table") {
    const headers = [..._qsTableColumns];
    const rows = [];
    document.querySelectorAll("#qs-table-rows .qs-table-row").forEach(row => {
      const cells = Array.from(row.querySelectorAll("input.qs-tbl-cell")).map(inp => inp.value.trim());
      if (cells.some(c => c)) rows.push({ cells });
    });
    if (rows.length) {
      return [{ _col_headers: true, headers }, ...rows];
    }
    return rows;
  }
  return [];
}

async function _onQsAddConfirm() {
  const heading = el.qsNewHeading().value.trim();
  if (!heading) { toast("Section heading is required", "error"); el.qsNewHeading().focus(); return; }

  const content = _qsCollectContent();
  if (!content.length) { toast("Please add at least one content item", "error"); return; }

  const btn = el.btnQsAddConfirm();
  btn.disabled = true; btn.textContent = "Adding...";

  try {
    const r = await api("/api/bhc/admin/quotation-sections", {
      method: "POST",
      body: JSON.stringify({ heading, content_type: _qsActiveType, content }),
    });
    const data = await r.json();

    // Insert at chosen position
    const insertAfterVal = el.qsInsertAfter().value;
    if (insertAfterVal === "end") {
      _qsLocalSections.push(data.section);
    } else {
      const afterIdx = _qsLocalSections.findIndex(s => s.id === Number(insertAfterVal));
      if (afterIdx >= 0) {
        _qsLocalSections.splice(afterIdx + 1, 0, data.section);
      } else {
        _qsLocalSections.push(data.section);
      }
      // Auto-save reorder so position persists
      const orderedIds = _qsLocalSections.map(s => s.id);
      await api("/api/bhc/admin/quotation-sections/reorder", {
        method: "PUT",
        body: JSON.stringify({ ordered_ids: orderedIds }),
      });
    }

    _renderQSItems();
    _qsCloseModal();
    toast("Section added successfully!", "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Add Section";
  }
}

async function onSaveQSections() {
  // Save reorder (the main save action)
  try {
    setAdminFeedback("Saving section order...", "info");
    const orderedIds = _qsLocalSections.map(s => s.id);
    const r = await api("/api/bhc/admin/quotation-sections/reorder", {
      method: "PUT",
      body: JSON.stringify({ ordered_ids: orderedIds }),
    });
    const data = await r.json();
    state.adminConfig.quotation_sections = data.quotation_sections;
    renderQSSectionsList();
    setAdminFeedback("Section order saved.", "success");
    toast("Sections saved", "success");
    lockAdminSection("qsections");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

let authMode = "login"; // "login" or "register"

function toggleAuthMode(mode) {
  authMode = mode || (authMode === "login" ? "register" : "login");
  const isRegister = authMode === "register";
  el.loginFormSection().classList.toggle("hidden", isRegister);
  el.forgotPasswordPanel().classList.add("hidden");
  el.registerFormSection().classList.toggle("hidden", !isRegister);
  el.authDivider().textContent = isRegister ? "Create Account" : "Secure Sign-In";
  el.btnAuthToggle().textContent = isRegister ? "Sign In" : "Create Account";
  el.authToggleText().textContent = isRegister ? "Already have an account?" : "Don't have an account?";
  setAuthFeedback("", "");

  if (isRegister) {
    // Populate security questions dropdown
    loadRegSecurityQuestions();
  }
}

async function loadRegSecurityQuestions() {
  try {
    const r = await api("/api/bhc/auth/security-questions");
    const data = await r.json();
    const sel = el.regSecurityQuestion();
    if (sel && data.questions) {
      sel.innerHTML = '<option value="">— Select a question —</option>' +
        data.questions.map(q => `<option value="${escHtml(q)}">${escHtml(q)}</option>`).join("");
    }
  } catch (_) {}
}

function evaluateRegPassword() {
  const password = el.regPassword().value;
  const confirm = el.regConfirmPassword().value;

  const checks = {
    length:  password.length >= 8,
    upper:   /[A-Z]/.test(password),
    lower:   /[a-z]/.test(password),
    digit:   /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
  const score = Object.values(checks).filter(Boolean).length;

  setPolicyState(el.regPolicyLength(),  checks.length);
  setPolicyState(el.regPolicyUpper(),   checks.upper);
  setPolicyState(el.regPolicyLower(),   checks.lower);
  setPolicyState(el.regPolicyDigit(),   checks.digit);
  setPolicyState(el.regPolicySpecial(), checks.special);
  setPolicyState(el.regPolicyMatch(),   password.length > 0 && password === confirm);

  // Strength bar
  const fill = document.getElementById("reg-strength-fill");
  const label = document.getElementById("reg-strength-label");
  if (fill && label) {
    if (!password) {
      fill.style.width = "0";
      fill.style.background = "";
      label.textContent = "";
      label.style.color = "";
    } else if (score <= 2) {
      fill.style.width = "25%";
      fill.style.background = "#ef4444";
      label.textContent = "Weak";
      label.style.color = "#ef4444";
    } else if (score <= 4) {
      fill.style.width = "60%";
      fill.style.background = "#f59e0b";
      label.textContent = "Medium";
      label.style.color = "#f59e0b";
    } else {
      fill.style.width = "100%";
      fill.style.background = "#22c55e";
      label.textContent = "Strong";
      label.style.color = "#22c55e";
    }
  }
}

function checkPasswordPolicy(password) {
  if (password.length < 8) return "Password must be at least 8 characters long.";
  if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter.";
  if (!/\d/.test(password)) return "Password must contain at least one digit.";
  if (!/[^A-Za-z0-9]/.test(password)) return "Password must contain at least one special character (e.g. @, #, !, $).";
  return null;
}

async function onRegister() {
  const fullName = el.regFullName().value.trim();
  const email = el.regEmail().value.trim();
  const designation = el.regDesignation().value.trim();
  const password = el.regPassword().value;
  const confirmPassword = el.regConfirmPassword().value;
  const securityQuestion = el.regSecurityQuestion().value;
  const securityAnswer = el.regSecurityAnswer().value.trim();

  if (!fullName || !email || !password) {
    setAuthFeedback("Full name, email, and password are required.", "error");
    return;
  }
  if (password !== confirmPassword) {
    setAuthFeedback("Passwords do not match.", "error");
    return;
  }
  const policyError = checkPasswordPolicy(password);
  if (policyError) {
    setAuthFeedback(policyError, "error");
    return;
  }
  if (!securityQuestion || !securityAnswer) {
    setAuthFeedback("Security question and answer are required.", "error");
    return;
  }

  const btn = el.btnRegister();
  try {
    btnLoading(btn, true);
    setAuthFeedback("Creating your account...", "info");
    const r = await api("/api/bhc/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
        designation,
        security_question: securityQuestion,
        security_answer: securityAnswer,
      }),
    });
    const data = await r.json();

    // Clear form
    el.regFullName().value = "";
    el.regEmail().value = "";
    el.regDesignation().value = "";
    el.regPassword().value = "";
    el.regConfirmPassword().value = "";
    el.regSecurityQuestion().value = "";
    el.regSecurityAnswer().value = "";

    setAuthFeedback(data.message || "Registration successful. Awaiting admin approval.", "success");
    toast("Account created — pending approval", "success");

    // Switch back to login view after a short delay
    setTimeout(() => toggleAuthMode("login"), 3000);
  } catch (err) {
    setAuthFeedback(err.message, "error");
    toast(err.message, "error");
  } finally {
    btnLoading(btn, false);
  }
}

async function onLogin() {
  const email = el.loginEmail().value.trim();
  const password = el.loginPassword().value;
  if (!email || !password) {
    setAuthFeedback("Enter your email and password.", "error");
    return;
  }

  const btn = el.btnLogin();
  try {
    btnLoading(btn, true);
    setAuthFeedback("Signing in...", "info");
    await api("/api/bhc/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    el.loginPassword().value = "";
    await loadSession();
    await refreshAll();
    if (state.session?.is_admin) {
      await loadAdminConfig();
    }
    setAuthFeedback("Login successful.", "success");
    notify("Welcome back", state.session?.full_name || "You are signed in.", "success", 4000);

    // Restore last active tab
    try {
      const savedTab = localStorage.getItem(TAB_STORAGE_KEY);
      if (savedTab && ["overview","enquiries","studio","pipeline","deq","admin"].includes(savedTab)) {
        activateTab(savedTab);
      }
    } catch (_) {}

    if (state.session?.must_change_password) {
      setAccountFeedback("Your password was reset by admin. Change it now.", "info");
      activateTab("overview");
      notify("Password Change Required", "Your password was reset. Please update it from your profile.", "warning", 0);
    }

    // Populate security questions dropdown
    try {
      const sqR = await api("/api/bhc/auth/security-questions");
      const sqData = await sqR.json();
      const selectEl = el.profileSecurityQuestion();
      if (selectEl && sqData.questions) {
        selectEl.innerHTML = '<option value="">— Select a question —</option>' +
          sqData.questions.map(q => `<option value="${escHtml(q)}">${escHtml(q)}</option>`).join("");
      }
    } catch (_) {}

    // Prompt to set security question if not set
    if (state.session?.authenticated && !state.session?.has_security_question) {
      notify(
        "Security Question Required",
        "Set a security question from your profile to enable password recovery.",
        "warning",
        0,
      );
    }
    if (el.profileSqStatus()) {
      el.profileSqStatus().textContent = state.session?.has_security_question ? "(Set ✓)" : "(Not set)";
    }
  } catch (err) {
    setAuthFeedback(err.message, "error");
    toast(err.message, "error");
  } finally {
    btnLoading(btn, false);
  }
}

async function onLogout() {
  try {
    await api("/api/bhc/auth/logout", { method: "POST" });
    state.adminConfig = null;
    state.pending = [];
    state.pendingFiltered = [];
    state.processed = [];
    state.processedFiltered = [];
    await loadSession();
    setAuthFeedback("Logged out successfully.", "info");
    toast("Logged out", "success");
  } catch (err) {
    setAuthFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

async function onForgotLookup() {
  const email = el.forgotEmail().value.trim();
  if (!email) {
    setAuthFeedback("Enter your email address.", "error");
    return;
  }
  try {
    setAuthFeedback("Looking up your account…", "info");
    const r = await api("/api/bhc/auth/security-question/lookup", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    const data = await r.json();
    el.forgotQuestionLabel().textContent = data.question;
    el.forgotStepEmail().classList.add("hidden");
    el.forgotStepAnswer().classList.remove("hidden");
    setAuthFeedback("", "");
  } catch (err) {
    setAuthFeedback(err.message, "error");
  }
}

function onForgotBack() {
  el.forgotStepAnswer().classList.add("hidden");
  el.forgotStepEmail().classList.remove("hidden");
  setAuthFeedback("", "");
}

async function onForgotPassword() {
  const email = el.forgotEmail().value.trim();
  const answer = el.forgotAnswer().value.trim();
  const newPassword = el.forgotNewPassword().value;
  const confirmPassword = el.forgotConfirmPassword().value;

  if (!email || !answer || !newPassword || !confirmPassword) {
    setAuthFeedback("All fields are required.", "error");
    return;
  }

  if (newPassword !== confirmPassword) {
    setAuthFeedback("New password and confirm password do not match.", "error");
    return;
  }
  const policyError = checkPasswordPolicy(newPassword);
  if (policyError) {
    setAuthFeedback(policyError, "error");
    return;
  }

  try {
    setAuthFeedback("Verifying and resetting password…", "info");
    await api("/api/bhc/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email, new_password: newPassword, security_answer: answer }),
    });
    el.forgotEmail().value = "";
    el.forgotAnswer().value = "";
    el.forgotNewPassword().value = "";
    el.forgotConfirmPassword().value = "";
    toggleForgotPasswordPanel(false);
    setAuthFeedback("Password updated successfully. Sign in with your new password.", "success");
    toast("Password reset successful", "success");
  } catch (err) {
    setAuthFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

async function onChangePassword() {
  const evaluation = evaluateChangePassword();
  const { currentPassword, newPassword, confirmPassword } = evaluation;

  if (!currentPassword || !newPassword || !confirmPassword) {
    setAccountFeedback("Fill all password fields.", "error");
    return;
  }
  if (!evaluation.checks.length || !evaluation.checks.upper || !evaluation.checks.lower || !evaluation.checks.digit || !evaluation.checks.special) {
    setAccountFeedback("New password does not meet policy requirements.", "error");
    return;
  }
  if (!evaluation.checks.different) {
    setAccountFeedback("New password must be different from current password.", "error");
    return;
  }
  if (newPassword !== confirmPassword) {
    setAccountFeedback("New password and confirm password do not match.", "error");
    return;
  }

  try {
    setAccountFeedback("Changing password...", "info");
    const r = await api("/api/bhc/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    const data = await r.json();
    el.changeCurrentPassword().value = "";
    el.changeNewPassword().value = "";
    el.changeConfirmPassword().value = "";
    evaluateChangePassword();
    state.adminConfig = null;
    await loadSession();
    setAccountFeedback(data.message, "success");
    setAuthFeedback("Please sign in again with the new password.", "info");
    closeProfileMenu();
    toast("Password changed. Sign in again.", "success");
  } catch (err) {
    setAccountFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

function companyPayload() {
  return {
    company_name: el.adminCompanyName().value.trim(),
    company_subtitle: el.adminCompanySubtitle().value.trim(),
    company_address: el.adminCompanyAddress().value.trim(),
    company_phone: el.adminCompanyPhone().value.trim(),
    company_email: el.adminCompanyEmail().value.trim(),
    contact_name: el.adminContactName().value.trim(),
    urgency_surcharge_percent: document.getElementById("admin-urgency-surcharge").value.trim() || "10",
    gst_percent: document.getElementById("admin-gst-percent").value.trim() || "18",
  };
}

function documentPayload() {
  return {
    company_profile_paragraphs: splitLines(el.adminCompanyProfile().value),
    tuv_history_paragraphs: splitLines(el.adminTuvHistory().value),
    service_capabilities: splitLines(el.adminServiceCapabilities().value),
    deliverables: splitLines(el.adminDeliverables().value),
    payment_terms: splitLines(el.adminPaymentTerms().value),
    other_terms: splitLines(el.adminOtherTerms().value),
    system_generated_note: el.adminSystemNote().value.trim(),
  };
}

async function onSaveCompany() {
  try {
    setAdminFeedback("Saving company details...", "info");
    const r = await api("/api/bhc/admin/company", {
      method: "PUT",
      body: JSON.stringify(companyPayload()),
    });
    state.adminConfig.company = await r.json();
    setAdminFeedback("Company details saved.", "success");
    toast("Company details saved", "success");
    lockAdminSection("company");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

async function onSaveDocument() {
  try {
    setAdminFeedback("Saving quotation content...", "info");
    const r = await api("/api/bhc/admin/document", {
      method: "PUT",
      body: JSON.stringify(documentPayload()),
    });
    state.adminConfig.document = await r.json();
    populateAdminForm();
    setAdminFeedback("Quotation content saved.", "success");
    toast("Quotation content saved", "success");
    lockAdminSection("document");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

async function onSavePricing() {
  try {
    const allSlabs = state.adminConfig?.pricing?.slabs || [];
    const allNewSlabs = state.adminConfig?.pricing?.new_building_slabs || [];

    // Front-end validation
    for (const [i, s] of allSlabs.entries()) {
      if (!String(s.label || "").trim()) {
        setAdminFeedback(`Building slab ${i + 1}: Label is required.`, "error");
        toast(`Building slab ${i + 1}: Label is required`, "error");
        // Highlight the offending row
        const row = el.adminPricingBody()?.rows[i];
        if (row) { row.classList.add("slab-row-error"); setTimeout(() => row.classList.remove("slab-row-error"), 3000); }
        return;
      }
      if (Number(s.min_area) > Number(s.max_area)) {
        setAdminFeedback(`Building slab ${i + 1}: Min area cannot be greater than Max area.`, "error");
        toast(`Building slab ${i + 1}: Min > Max`, "error");
        return;
      }
    }
    for (const [i, s] of allNewSlabs.entries()) {
      if (!String(s.label || "").trim()) {
        setAdminFeedback(`New Building slab ${i + 1}: Label is required.`, "error");
        toast(`New Building slab ${i + 1}: Label is required`, "error");
        const row = el.adminNewBuildingPricingBody()?.rows[i];
        if (row) { row.classList.add("slab-row-error"); setTimeout(() => row.classList.remove("slab-row-error"), 3000); }
        return;
      }
      if (Number(s.min_area) > Number(s.max_area)) {
        setAdminFeedback(`New Building slab ${i + 1}: Min area cannot be greater than Max area.`, "error");
        toast(`New Building slab ${i + 1}: Min > Max`, "error");
        return;
      }
    }

    setAdminFeedback("Saving pricing slabs...", "info");
    const r = await api("/api/bhc/admin/pricing", {
      method: "PUT",
      body: JSON.stringify({
        slabs: allSlabs.map(({ _new: _, ...s }) => s),
        new_building_slabs: allNewSlabs.map(({ _new: _, ...s }) => s),
      }),
    });
    state.adminConfig.pricing = await r.json();
    renderAdminPricingRows();
    setAdminFeedback("Pricing slabs saved.", "success");
    toast("Pricing slabs saved", "success");
    lockAdminSection("pricing");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

async function onCreateUser() {
  const payload = {
    full_name: el.adminUserFullName().value.trim(),
    email: el.adminUserEmail().value.trim(),
    password: el.adminUserPassword().value,
    is_admin: el.adminUserIsAdmin().checked,
    designation: el.adminUserDesignation().value.trim(),
  };

  if (!payload.full_name || !payload.email || !payload.password) {
    setAdminFeedback("Full name, email, and temporary password are required to create a user.", "error");
    return;
  }

  try {
    setAdminFeedback("Creating user...", "info");
    await api("/api/bhc/admin/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // Upload signature if provided
    const sigFile = el.adminUserSignature().files?.[0];
    if (sigFile) {
      const form = new FormData();
      form.append("file", sigFile);
      // Note: signature is tied to the currently logged-in user's session.
      // For new users, admin can upload via the table after creation.
    }

    el.adminUserFullName().value = "";
    el.adminUserDesignation().value = "";
    el.adminUserEmail().value = "";
    el.adminUserPassword().value = "";
    el.adminUserSignature().value = "";
    el.adminUserIsAdmin().checked = false;
    await loadAdminConfig();
    setAdminFeedback("User created successfully.", "success");
    toast("User created", "success");
    lockAdminSection("users");
  } catch (err) {
    setAdminFeedback(err.message, "error");
    toast(err.message, "error");
  }
}

function onAddPricingRow() {
  if (!state.adminConfig?.pricing?.slabs) {
    state.adminConfig = state.adminConfig || {};
    state.adminConfig.pricing = state.adminConfig.pricing || { model: "area_slab", slabs: [], new_building_slabs: [] };
    state.adminConfig.pricing.slabs = state.adminConfig.pricing.slabs || [];
  }
  const lastSlab = state.adminConfig.pricing.slabs[state.adminConfig.pricing.slabs.length - 1];
  const nextMinArea = lastSlab ? Number(lastSlab.max_area || 0) + 1 : 0;
  state.adminConfig.pricing.slabs.push({
    min_area: nextMinArea,
    max_area: nextMinArea + 9999,
    label: "",
    quoted_price: 0,
    _new: true,
  });
  renderAdminPricingRows();
  // Scroll the new row into view
  const wrap = el.adminPricingBody().closest(".admin-table-wrap");
  if (wrap) wrap.scrollTop = wrap.scrollHeight;
}

function onAddNewBuildingPricingRow() {
  if (!state.adminConfig?.pricing?.new_building_slabs) {
    state.adminConfig = state.adminConfig || {};
    state.adminConfig.pricing = state.adminConfig.pricing || { model: "area_slab", slabs: [], new_building_slabs: [] };
    state.adminConfig.pricing.new_building_slabs = state.adminConfig.pricing.new_building_slabs || [];
  }
  const slabs = state.adminConfig.pricing.new_building_slabs;
  const lastSlab = slabs[slabs.length - 1];
  const nextMinArea = lastSlab ? Number(lastSlab.max_area || 0) + 1 : 0;
  slabs.push({
    min_area: nextMinArea,
    max_area: nextMinArea + 9999,
    label: "",
    quoted_price: 0,
    _new: true,
  });
  renderAdminPricingRows();
  // Scroll the new row into view
  const wrap = el.adminNewBuildingPricingBody().closest(".admin-table-wrap");
  if (wrap) wrap.scrollTop = wrap.scrollHeight;
}

/* ── Admin Section Edit/Lock Toggle ── */

function lockAdminSection(section) {
  const card = document.querySelector(`[data-admin-section="${section}"]`);
  if (!card) return;
  card.classList.add("admin-locked");
  card.querySelectorAll("input, textarea, select").forEach(el => {
    el.disabled = true;
    el.classList.add("admin-disabled");
  });
  const editBtn = card.querySelector(`[data-edit-section="${section}"]`);
  const cancelBtn = card.querySelector(`[data-cancel-section="${section}"]`);
  if (editBtn) editBtn.classList.remove("hidden");
  if (cancelBtn) cancelBtn.classList.add("hidden");
  // Hide save/action buttons
  card.querySelectorAll(".btn-primary, #btn-add-pricing-row, #btn-add-new-building-pricing-row, #btn-add-qs").forEach(btn => btn.classList.add("hidden"));
  // Hide delete buttons inside pricing table
  card.querySelectorAll("[data-delete-pricing-index], [data-delete-nbpricing-index]").forEach(btn => btn.classList.add("hidden"));
}

function unlockAdminSection(section) {
  const card = document.querySelector(`[data-admin-section="${section}"]`);
  if (!card) return;
  card.classList.remove("admin-locked");
  card.querySelectorAll("input, textarea, select").forEach(el => {
    el.disabled = false;
    el.classList.remove("admin-disabled");
  });
  const editBtn = card.querySelector(`[data-edit-section="${section}"]`);
  const cancelBtn = card.querySelector(`[data-cancel-section="${section}"]`);
  if (editBtn) editBtn.classList.add("hidden");
  if (cancelBtn) cancelBtn.classList.remove("hidden");
  // Show save/action buttons
  card.querySelectorAll(".btn-primary, #btn-add-pricing-row, #btn-add-new-building-pricing-row, #btn-add-qs").forEach(btn => btn.classList.remove("hidden"));
  // Show delete buttons inside pricing table
  card.querySelectorAll("[data-delete-pricing-index], [data-delete-nbpricing-index]").forEach(btn => btn.classList.remove("hidden"));
}

function lockAllAdminSections() {
  document.querySelectorAll("[data-admin-section]").forEach(card => {
    lockAdminSection(card.dataset.adminSection);
  });
}

function bindAdminEditButtons() {
  document.querySelectorAll("[data-edit-section]").forEach(btn => {
    btn.addEventListener("click", () => unlockAdminSection(btn.dataset.editSection));
  });
  document.querySelectorAll("[data-cancel-section]").forEach(btn => {
    btn.addEventListener("click", () => {
      lockAdminSection(btn.dataset.cancelSection);
      // Re-populate form to discard any edits
      if (state.adminConfig) populateAdminForm();
    });
  });
}

function updateAdminEditVisibility() {
  const isAdmin = !!state.session?.is_admin;
  document.querySelectorAll(".admin-only").forEach(el => {
    el.classList.toggle("hidden", !isAdmin);
  });
}

async function init() {
  bindTabs();
  bindProfileMenu();
  bindPasswordToggles();

  // Auth show-password checkbox
  const showPwCb = document.getElementById("auth-show-pw");
  if (showPwCb) {
    showPwCb.addEventListener("change", () => {
      const pw = el.loginPassword();
      if (pw) pw.type = showPwCb.checked ? "text" : "password";
    });
  }

  el.btnLogin().addEventListener("click", onLogin);
  el.btnAuthToggle().addEventListener("click", () => toggleAuthMode());
  el.btnRegister().addEventListener("click", onRegister);
  [el.regPassword(), el.regConfirmPassword()].forEach(input => {
    input.addEventListener("input", evaluateRegPassword);
  });
  // Eye-toggle buttons on registration form
  document.querySelectorAll(".auth-pw-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      // Swap SVG visibility (first = eye-open, second = eye-slash)
      const svgs = btn.querySelectorAll("svg");
      if (svgs.length === 2) {
        svgs[0].classList.toggle("hidden", isHidden);
        svgs[1].classList.toggle("hidden", !isHidden);
      }
    });
  });
  el.btnForgotPasswordToggle().addEventListener("click", () => toggleForgotPasswordPanel());
  el.btnForgotLookup().addEventListener("click", onForgotLookup);
  el.btnForgotBack().addEventListener("click", onForgotBack);
  el.btnForgotPassword().addEventListener("click", onForgotPassword);
  const btnOpenPasswordPanel = el.btnOpenPasswordPanel();
  if (btnOpenPasswordPanel) {
    btnOpenPasswordPanel.addEventListener("click", () => toggleProfilePasswordPanel());
  }
  el.btnLogout().addEventListener("click", onLogout);

  // Profile save (designation + signature)
  const btnSaveProfile = el.btnSaveProfile();
  if (btnSaveProfile) {
    btnSaveProfile.addEventListener("click", async () => {
      try {
        // Save designation + security question
        const profileBody = { designation: el.profileDesignation().value.trim() };
        const sq = el.profileSecurityQuestion().value;
        const sa = el.profileSecurityAnswer().value.trim();
        if (sq && sa) {
          profileBody.security_question = sq;
          profileBody.security_answer = sa;
        }
        await api("/api/bhc/user/profile", {
          method: "PUT",
          body: JSON.stringify(profileBody),
        });

        // Upload signature if file selected
        const sigFile = el.profileSignatureFile().files?.[0];
        if (sigFile) {
          const form = new FormData();
          form.append("file", sigFile);
          const sigR = await fetch("/api/bhc/user/signature", {
            method: "POST",
            credentials: "include",
            body: form,
          });
          if (!sigR.ok) {
            const d = await sigR.json().catch(() => ({}));
            throw new Error(d.detail || "Signature upload failed");
          }
          el.profileSignatureFile().value = "";
        }

        el.profileSecurityAnswer().value = "";
        await loadSession();
        toast("Profile saved", "success");
      } catch (err) {
        toast(err.message, "error");
      }
    });
  }

  el.pendingSearch().addEventListener("input", applyPendingFilters);
  el.pendingPropertyFilter().addEventListener("change", applyPendingFilters);

  el.processedSearch().addEventListener("input", applyProcessedFilters);
  el.processedStatusFilter().addEventListener("change", applyProcessedFilters);
  el.processedPaymentFilter().addEventListener("change", applyProcessedFilters);
  el.processedPropertyFilter().addEventListener("change", applyProcessedFilters);
  el.processedDateFrom().addEventListener("change", applyProcessedFilters);
  el.processedDateTo().addEventListener("change", applyProcessedFilters);

  // Date field clear buttons
  document.querySelectorAll(".date-clear-btn").forEach(btn => {
    const input = document.getElementById(btn.dataset.target);
    if (!input) return;
    const wrap = btn.closest(".date-field-wrap");
    // Keep has-value class in sync
    const syncState = () => wrap.classList.toggle("has-value", !!input.value);
    input.addEventListener("change", () => { syncState(); applyProcessedFilters(); });
    btn.addEventListener("click", () => {
      input.value = "";
      syncState();
      applyProcessedFilters();
    });
  });

  el.btnGenerate().addEventListener("click", onGenerateQuote);
  el.btnDownloadPdf().addEventListener("click", () => onDownload("pdf"));
  el.btnSendEmail().addEventListener("click", openEmailDraft);
  el.previewClose().addEventListener("click", closePreviewModal);
  el.previewCancel().addEventListener("click", closePreviewModal);
  el.previewInsertSig().addEventListener("click", onInsertSignatureAndDownload);
  [el.changeCurrentPassword(), el.changeNewPassword(), el.changeConfirmPassword()].forEach((input) => {
    input.addEventListener("input", evaluateChangePassword);
  });
  el.btnChangePassword().addEventListener("click", onChangePassword);
  el.btnRefresh().addEventListener("click", onRefresh);
  el.btnExport().addEventListener("click", onExport);
  el.btnSaveCompany().addEventListener("click", onSaveCompany);
  el.btnSaveDocument().addEventListener("click", onSaveDocument);
  el.btnSavePricing().addEventListener("click", onSavePricing);
  el.btnAddPricingRow().addEventListener("click", onAddPricingRow);
  el.btnAddNewBuildingPricingRow().addEventListener("click", onAddNewBuildingPricingRow);
  el.btnCreateUser().addEventListener("click", onCreateUser);
  el.btnSaveScope().addEventListener("click", onSaveScope);
  el.btnSaveQSections().addEventListener("click", onSaveQSections);
  el.btnAddQs().addEventListener("click", _openQsAddModal);
  el.btnQsAddConfirm().addEventListener("click", _onQsAddConfirm);
  el.btnQsAddCancel().addEventListener("click", _qsCloseModal);
  // Modal overlay & close button
  document.querySelectorAll("[data-qs-modal-close]").forEach(el => el.addEventListener("click", _qsCloseModal));
  // Close modal on overlay background click (not card)
  el.qsAddModal().addEventListener("click", (e) => { if (e.target === el.qsAddModal()) _qsCloseModal(); });
  // Content type card selection
  document.querySelectorAll(".qs-type-card").forEach(card => {
    card.addEventListener("click", () => _qsSetActiveType(card.dataset.typeValue));
  });
  // Builder add-item buttons
  document.getElementById("btn-qs-add-item").addEventListener("click", () => _qsAddBuilderItem("list"));
  document.getElementById("btn-qs-add-para").addEventListener("click", () => _qsAddBuilderItem("paragraph"));
  document.getElementById("btn-qs-add-row").addEventListener("click", () => _qsAddBuilderItem("table"));
  el.btnLoadAudit().addEventListener("click", loadAuditLogs);
  el.auditFilterType().addEventListener("change", renderAuditLogs);
  document.addEventListener("visibilitychange", onVisibilityChange);
  window.addEventListener("focus", onWindowFocus);

  bindAdminEditButtons();
  lockAllAdminSections();
  bindKeyboardShortcuts();

  // Set footer year
  const footerYear = document.getElementById("footer-year");
  if (footerYear) footerYear.textContent = new Date().getFullYear();

  await loadSession();
  if (state.session?.authenticated) {
    await refreshAll();
  }
  if (state.session?.authenticated && state.session?.is_admin) {
    await loadAdminConfig();
  }
  evaluateChangePassword();
  startAutoRefresh();
  startSessionHealthCheck();
  checkSystemHealth();
  setInterval(checkSystemHealth, 60000);

  // Show footer after auth
  const footer = document.getElementById("app-footer");
  if (footer) footer.style.display = "";
}

function hasUnsavedPipelineChanges() {
  return Object.values(state.processedSync).some((sync) => sync === "dirty" || sync === "saving");
}

async function refreshLiveView() {
  if (!state.session?.authenticated || state.isAutoRefreshing || document.hidden) {
    return;
  }

  state.isAutoRefreshing = true;
  try {
    const tasks = [loadDashboard()];

    if (state.activeTab === "overview" || state.activeTab === "enquiries" || state.activeTab === "studio") {
      tasks.push(loadPending());
    }

    if (state.activeTab === "pipeline" && !hasUnsavedPipelineChanges()) {
      tasks.push(loadProcessed());
    }

    await Promise.all(tasks);
  } catch (_err) {
    // Silent on auto-refresh to avoid noisy toasts during intermittent network issues.
  } finally {
    state.isAutoRefreshing = false;
  }
}

function startAutoRefresh() {
  if (state.autoRefreshTimer) {
    clearInterval(state.autoRefreshTimer);
  }
  state.autoRefreshTimer = setInterval(refreshLiveView, AUTO_REFRESH_MS);
}

function onVisibilityChange() {
  if (!document.hidden) {
    refreshLiveView();
  }
}

function onWindowFocus() {
  refreshLiveView();
}

async function refreshAll() {
  if (!state.session?.authenticated) {
    return;
  }
  await Promise.all([
    loadExcelStatus(),
    loadDashboard(),
    loadPending(),
    loadProcessed(),
  ]);
  updateLastRefreshed();
}

async function onRefresh() {
  if (!state.session?.authenticated) {
    return;
  }
  const btn = el.btnRefresh();
  try {
    btnLoading(btn, true);
    await refreshAll();
    if (state.session?.authenticated && state.session?.is_admin) {
      await loadAdminConfig();
    }
    toast("Dashboard refreshed", "success");
  } catch (err) {
    toast("Refresh failed: " + err.message, "error");
  } finally {
    btnLoading(btn, false);
  }
}

async function loadDashboard() {
  try {
    const r = await api("/api/bhc/dashboard");
    const d = await r.json();

    animateCounter(el.mTotal(), d.total_enquiries ?? 0);
    animateCounter(el.mPending(), d.pending ?? 0);
    animateCounter(el.mQuoted(), d.quoted ?? 0);
    animateCounter(el.mConverted(), d.converted ?? 0);
    el.mQuotedRevenue().textContent = fmtINR(d.quoted_revenue ?? d.revenue ?? 0);
    el.mConvertedRevenue().textContent = fmtINR(d.converted_revenue ?? 0);
  } catch (err) {
    if (!isMissingExcelError(err)) {
      throw err;
    }

    el.mTotal().textContent = 0;
    el.mPending().textContent = 0;
    el.mQuoted().textContent = 0;
    el.mConverted().textContent = 0;
    el.mQuotedRevenue().textContent = fmtINR(0);
    el.mConvertedRevenue().textContent = fmtINR(0);
  }
}

async function loadPending() {
  try {
    const r = await api("/api/bhc/clients/pending");
    const d = await r.json();
    state.pending = d.clients || [];
    el.pendingCount().textContent = d.count || 0;

    updatePendingPropertyFilter();
    applyPendingFilters();
    updateHeroStats();
  } catch (err) {
    if (!isMissingExcelError(err)) {
      throw err;
    }

    state.pending = [];
    state.pendingFiltered = [];
    el.pendingCount().textContent = 0;
    updatePendingPropertyFilter();
    renderPending([]);
    updateHeroStats();
    el.pendingBody().innerHTML = '<tr><td colspan="8" class="muted">No enquiry workbook found on OneDrive. Check the .env EXCEL_FILE_PATH setting.</td></tr>';
  }
}

function renderPending(rows) {
  const body = el.pendingBody();
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="8" class="muted">No pending clients match current filters.</td></tr>';
    return;
  }

  const q = el.pendingSearch().value.trim();

  body.innerHTML = rows.map((c, idx) => `
    <tr>
      <td>${highlightText(c.name, q)}</td>
      <td>${highlightText(c.phone, q)}</td>
      <td>${escHtml(c.property_type)}</td>
      <td>${escHtml(c.building_system || "-")}</td>
      <td>${escHtml(c.area_sqft)}</td>
      <td>${escHtml(c.building_age || "-")}</td>
      <td>${escHtml(c.urgency || "-")}</td>
      <td><button class="btn btn-sm btn-primary" data-pending-index="${idx}"><svg width=\"12\" height=\"12\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.5\"><polyline points=\"9 18 15 12 9 6\"/></svg> Select</button></td>
    </tr>
  `).join("");

  body.querySelectorAll("button[data-pending-index]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const index = Number(btn.dataset.pendingIndex);
      await selectPending(state.pendingFiltered[index]);
      activateTab("studio");
    });
  });
}

async function selectPending(c) {
  let selectedClient = c;

  try {
    const params = new URLSearchParams();
    if (c.phone) params.set("phone", c.phone);
    if (c.timestamp) params.set("timestamp", c.timestamp);

    const r = await api(`/api/bhc/client/${encodeURIComponent(c.name)}?${params.toString()}`);
    const full = await r.json();
    selectedClient = {
      ...c,
      name: full.Client_Name || c.name,
      phone: full.Phone_Number || c.phone,
      location: full.Location || c.location,
      property_type: full.Property_Type || c.property_type,
      building_system: full.Building_System || c.building_system,
      area_sqft: full.Area_sqft || c.area_sqft,
      area_numeric: Number(full._area_numeric || c.area_numeric || 0),
      issue_observed: full.Issue_Observed || c.issue_observed,
      building_age: full.Building_Age || c.building_age,
      urgency: full.Urgency || c.urgency || "",
      notes: full.Notes || c.notes,
      timestamp: full.Timestamp || c.timestamp,
    };
  } catch (_err) {
    // Keep existing list data if detail fetch fails.
  }

  state.selected = selectedClient;
  state.generatedQuote = null;
  setFeedback("");

  el.detailEmpty().classList.add("hidden");
  el.detailPanel().classList.remove("hidden");

  el.dName().textContent = selectedClient.name || "-";
  el.dPhone().textContent = selectedClient.phone || "-";
  el.dLocation().textContent = selectedClient.location || "-";
  el.dProperty().textContent = selectedClient.property_type || "-";
  el.dStructure().textContent = selectedClient.building_system || "-";

  const bsLabel = selectedClient.building_system || "";
  const inferredServiceName = bsLabel === "Steel"
    ? "BHC - PEB Steel Structure"
    : bsLabel === "Both"
      ? "BHC - Combined Structure (RCC + PEB Steel)"
      : bsLabel === "RCC"
        ? "BHC - RCC Buildings"
        : "Building Health Check";
  el.dServiceName().textContent = inferredServiceName;
  el.dStructurePreview().textContent = bsLabel || "-";
  el.dArea().textContent = `${selectedClient.area_sqft || "0"} sq.ft`;
  el.dIssue().textContent = selectedClient.issue_observed || "-";
  el.dAge().textContent = selectedClient.building_age || "-";
  document.getElementById("d-urgency").textContent = selectedClient.urgency || "-";
  document.getElementById("d-price-base").textContent = "₹ 0.00";
  document.getElementById("d-gst-amount").textContent = "₹ 0.00";
  document.getElementById("d-urgency-row").classList.add("hidden");
  el.dPrice().textContent = "₹ 0.00";
  el.dRef().textContent = "-";
  el.discountPercent().value = "";

  el.btnGenerate().disabled = false;
  el.btnDownloadPdf().disabled = true;
  el.btnSendEmail().disabled = true;
}

async function onGenerateQuote() {
  if (!state.selected) {
    toast("Select a pending client first", "error");
    return;
  }

  const confirmed = await confirmAction({
    title: "Generate Quotation",
    message: `Generate quotation for ${state.selected.name}? This will record the client as processed.`,
    confirmText: "Generate",
    type: "info",
  });
  if (!confirmed) return;

  const btn = el.btnGenerate();
  try {
    btnLoading(btn, true);
    setFeedback("Generating quotation...", "info");
    const body = {
      client_name: state.selected.name,
      phone: state.selected.phone,
      property_type: state.selected.property_type,
      area: Number(state.selected.area_numeric || 0),
      building_system: state.selected.building_system || null,
      building_age: state.selected.building_age || null,
      timestamp: state.selected.timestamp || null,
      discount_percent: getDiscountPercentInput(),
    };

    const r = await api("/api/bhc/generate-quote", {
      method: "POST",
      body: JSON.stringify(body),
    });
    const data = await r.json();
    state.generatedQuote = data;

    document.getElementById("d-price-base").textContent = fmtINR(data?.pricing?.final_cost || 0);
    const gstPct = Number(data?.pricing?.gst_percent || 18);
    const gstAmt = Number(data?.pricing?.gst_amount || 0);
    const totalWithGst = Number(data?.pricing?.total_with_gst || 0);
    document.getElementById("d-gst-pct").textContent = gstPct;
    document.getElementById("d-gst-amount").textContent = fmtINR(gstAmt);
    el.dPrice().textContent = fmtINR(totalWithGst);

    // Show urgency surcharge row if applicable
    const urgencySurcharge = Number(data?.pricing?.urgency_surcharge_amount || 0);
    const urgencyRow = document.getElementById("d-urgency-row");
    if (urgencySurcharge > 0) {
      document.getElementById("d-urgency-surcharge").textContent = fmtINR(urgencySurcharge);
      urgencyRow.classList.remove("hidden");
    } else {
      urgencyRow.classList.add("hidden");
    }

    el.dStructurePreview().textContent = data?.pricing?.building_system || state.selected?.building_system || "-";
    el.dServiceName().textContent = data?.pricing?.service_name || "Building Health Check";
    el.dRef().textContent = data?.reference_number || "-";

    el.btnDownloadPdf().disabled = false;
    el.btnSendEmail().disabled = false;

    const usedDiscount = Number(data?.pricing?.discount_percent || 0);
    const discountMsg = usedDiscount > 0 ? ` Discount applied: ${usedDiscount}%` : "";
    setFeedback(`Quotation generated and stored as processed client.${discountMsg}`, "success");
    toast("Quote generated", "success");
    notify("Quotation Generated", `${state.selected.name} — ${fmtINR(totalWithGst)} (incl. GST)`, "success", 6000);

    await refreshAll();
  } catch (err) {
    setFeedback(err.message, "error");
    toast(err.message, "error");
  } finally {
    btnLoading(btn, false);
  }
}

function _buildDownloadBody() {
  return {
    client_name: state.selected.name,
    phone: state.selected.phone,
    property_type: state.selected.property_type,
    area: Number(state.selected.area_numeric || 0),
    building_system: state.selected.building_system || null,
    building_age: state.selected.building_age || null,
    timestamp: state.selected.timestamp || null,
    reference_number: state.generatedQuote?.reference_number || null,
    discount_percent: Number(state.generatedQuote?.pricing?.discount_percent || getDiscountPercentInput()),
  };
}

/** Open the preview modal with a signature-less PDF, then let the user insert sig & download. */
async function onDownload(format) {
  if (!state.selected) return;

  const modal = el.pdfPreviewModal();
  const frame = el.pdfPreviewFrame();
  const loading = el.previewLoading();
  const feedback = el.previewFeedback();

  // Reset modal state
  frame.src = "";
  loading.classList.remove("hidden");
  feedback.classList.add("hidden");
  feedback.textContent = "";
  modal.classList.remove("hidden");

  const body = _buildDownloadBody();

  try {
    // Fetch preview PDF (no signature)
    const r = await fetch("/api/bhc/preview/pdf", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || "Preview generation failed");
    }

    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    frame.src = url;
    // Clean up the object URL when the modal is closed later
    frame.dataset.blobUrl = url;
  } catch (err) {
    feedback.textContent = err.message;
    feedback.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
  }
}

/** Download final PDF with signature inserted. */
async function onInsertSignatureAndDownload() {
  // Check if user has uploaded a signature; if not, prompt them
  if (!state.session?.has_signature) {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".png,.jpg,.jpeg";
    fileInput.style.display = "none";
    document.body.appendChild(fileInput);

    const file = await new Promise((resolve) => {
      fileInput.addEventListener("change", () => resolve(fileInput.files?.[0] || null));
      fileInput.addEventListener("cancel", () => resolve(null));
      fileInput.click();
    });
    fileInput.remove();

    if (!file) {
      toast("Signature is required to download the final PDF.", "error");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);
      const uploadR = await fetch("/api/bhc/user/signature", {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!uploadR.ok) {
        const d = await uploadR.json().catch(() => ({}));
        throw new Error(d.detail || "Signature upload failed");
      }
      state.session.has_signature = true;
      toast("Signature uploaded successfully.", "success");
    } catch (err) {
      toast(err.message, "error");
      return;
    }
  }

  const feedback = el.previewFeedback();
  feedback.classList.add("hidden");

  const body = _buildDownloadBody();
  body.include_signature = true;

  try {
    const r = await fetch("/api/bhc/download/pdf", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || "Download failed");
    }

    const blob = await r.blob();
    const cd = r.headers.get("Content-Disposition") || "";
    const match = cd.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : "BHC_Quote.pdf";

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    closePreviewModal();
    toast("Downloaded " + filename, "success");
    activateTab("pipeline");
    await Promise.all([loadProcessed(), loadDashboard()]);
  } catch (err) {
    feedback.textContent = err.message;
    feedback.classList.remove("hidden");
  }
}

function closePreviewModal() {
  const modal = el.pdfPreviewModal();
  const frame = el.pdfPreviewFrame();
  if (frame.dataset.blobUrl) {
    URL.revokeObjectURL(frame.dataset.blobUrl);
    delete frame.dataset.blobUrl;
  }
  frame.src = "";
  modal.classList.add("hidden");
}

async function loadProcessed() {
  const r = await api("/api/bhc/clients/all");
  const d = await r.json();
  state.processed = d.clients || [];
  el.processedCount().textContent = d.count || 0;

  const nextSync = {};
  state.processed.forEach((row) => {
    const id = String(row.enquiry_id);
    const existing = state.processedSync[id];
    nextSync[id] = existing === "dirty" ? "dirty" : "saved";
  });
  state.processedSync = nextSync;

  updateProcessedPropertyFilter();
  applyProcessedFilters();
  updateHeroStats();
}

function renderProcessed(rows) {
  const body = el.processedBody();
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="10" class="muted">No processed records match current filters.</td></tr>';
    return;
  }

  body.innerHTML = rows.map((r, i) => `
    <tr class="row-sync-${getProcessedSync(r.enquiry_id)}" data-row-id="${escHtml(r.enquiry_id)}">
      <td>${escHtml(r.reference_number || "—")}</td>
      <td>${escHtml(r.client_name)}</td>
      <td>${escHtml(r.phone)}</td>
      <td>${escHtml(r.area)}</td>
      <td>${fmtINR(r.quoted_amount)}</td>
      <td>
        <select data-status-index="${i}">
          <option value="Quoted" ${r.status === "Quoted" ? "selected" : ""}>Quoted</option>
          <option value="Converted" ${r.status === "Converted" ? "selected" : ""}>Converted</option>
          <option value="Dropped" ${r.status === "Dropped" ? "selected" : ""}>Dropped</option>
        </select>
      </td>
      <td>
        <select data-payment-index="${i}">
          ${allowedPaymentsForStatus(r.status)
            .map((p) => `<option value="${p}" ${String(r.payment_status || "Pending") === p ? "selected" : ""}>${p}</option>`)
            .join("")}
        </select>
      </td>
      <td><input type="text" data-remarks-index="${i}" value="${escHtml(r.remarks || "")}" /></td>
      <td><span class="sync-pill ${getProcessedSync(r.enquiry_id)}" data-sync-index="${i}">${getSyncLabel(getProcessedSync(r.enquiry_id))}</span></td>
      <td><button class="btn btn-sm btn-outline" data-update-index="${i}" ${getProcessedSync(r.enquiry_id) === "dirty" ? "" : "disabled"}>Save</button></td>
    </tr>
  `).join("");

  const markDirty = (i) => {
    const row = rows[i];
    setProcessedSync(row.enquiry_id, "dirty");
    applyProcessedFilters();
  };

  body.querySelectorAll("select[data-status-index]").forEach((node) => {
    node.addEventListener("change", () => {
      const i = Number(node.dataset.statusIndex);
      rows[i].status = node.value;
      const allowed = allowedPaymentsForStatus(rows[i].status);
      if (!allowed.includes(rows[i].payment_status || "Pending")) {
        rows[i].payment_status = "Pending";
        toast(`Payment reset to Pending for ${rows[i].status} status.`, "info");
      }
      markDirty(i);
    });
  });

  body.querySelectorAll("select[data-payment-index]").forEach((node) => {
    node.addEventListener("change", () => {
      const i = Number(node.dataset.paymentIndex);
      const allowed = allowedPaymentsForStatus(rows[i].status);
      if (!allowed.includes(node.value)) {
        node.value = "Pending";
        rows[i].payment_status = "Pending";
        toast(`Only ${allowed.join("/")} allowed for ${rows[i].status} status.`, "error");
        markDirty(i);
        return;
      }
      rows[i].payment_status = node.value;
      markDirty(i);
    });
  });

  body.querySelectorAll("input[data-remarks-index]").forEach((node) => {
    node.addEventListener("change", () => {
      const i = Number(node.dataset.remarksIndex);
      rows[i].remarks = node.value;
      markDirty(i);
    });
  });

  body.querySelectorAll("button[data-update-index]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const i = Number(btn.dataset.updateIndex);
      const row = rows[i];
      const status = body.querySelector(`select[data-status-index="${i}"]`)?.value || null;
      const payment = body.querySelector(`select[data-payment-index="${i}"]`)?.value || null;
      const remarks = body.querySelector(`input[data-remarks-index="${i}"]`)?.value || "";

      if (!allowedPaymentsForStatus(status).includes(payment)) {
        toast(`Invalid combination: ${status} supports ${allowedPaymentsForStatus(status).join("/")} only.`, "error");
        return;
      }

      setProcessedSync(row.enquiry_id, "saving");
      applyProcessedFilters();

      try {
        await api("/api/bhc/update-status", {
          method: "POST",
          body: JSON.stringify({
            enquiry_id: row.enquiry_id,
            status,
            payment_status: payment,
            remarks,
          }),
        });
        setProcessedSync(row.enquiry_id, "saved");
        toast("Status updated", "success");
        await Promise.all([loadProcessed(), loadDashboard()]);
      } catch (err) {
        setProcessedSync(row.enquiry_id, "error");
        applyProcessedFilters();
        toast(err.message, "error");
      }
    });
  });
}

async function onExport() {
  if (hasUnsavedPipelineChanges()) {
    toast("Save pipeline changes before exporting.", "error");
    return;
  }

  try {
    const params = getProcessedExportParams();
    const exportUrl = params.toString() ? `/api/bhc/export?${params.toString()}` : "/api/bhc/export";
    const r = await fetch(exportUrl, { credentials: "include" });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || "Export failed");
    }

    const blob = await r.blob();
    const cd = r.headers.get("Content-Disposition") || "";
    const match = cd.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : "BHC_Processed.xlsx";

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast("Filtered export downloaded", "success");
  } catch (err) {
    toast(err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", init);

// ═══════════════════════════════════════════════════════════════════════════
// DEQ MODULE — Detailed Examination Quotation
// ═══════════════════════════════════════════════════════════════════════════

// Set to true to enable the DEQ tab; false shows the "Coming Soon" screen
const DEQ_ENABLED = false;

// ── DEQ DOM helpers ───────────────────────────────────────────────────────
const deqEl = {
  bhcSelect: () => document.getElementById("deq-bhc-select"),
  clientName: () => document.getElementById("deq-client-name"),
  phone: () => document.getElementById("deq-phone"),
  propertyType: () => document.getElementById("deq-property-type"),
  area: () => document.getElementById("deq-area"),
  examType: () => document.getElementById("deq-exam-type"),
  amount: () => document.getElementById("deq-amount"),
  issueDescription: () => document.getElementById("deq-issue-description"),
  formFeedback: () => document.getElementById("deq-form-feedback"),
  createdRef: () => document.getElementById("deq-created-ref"),
  btnCreate: () => document.getElementById("btn-create-deq"),
  btnExport: () => document.getElementById("btn-deq-export"),
  search: () => document.getElementById("deq-search"),
  statusFilter: () => document.getElementById("deq-status-filter"),
  body: () => document.getElementById("deq-body"),
  count: () => document.getElementById("deq-count"),
  mTotal: () => document.getElementById("deq-m-total"),
  mConverted: () => document.getElementById("deq-m-converted"),
  mRevenue: () => document.getElementById("deq-m-revenue"),
  mPaid: () => document.getElementById("deq-m-paid"),
  studioLocked: () => document.getElementById("deq-studio-locked"),
  studioContent: () => document.getElementById("deq-studio-content"),
  btnAddSection: () => document.getElementById("btn-add-deq-section"),
  qsList: () => document.getElementById("deq-qs-list"),
  // Add modal
  addModal: () => document.getElementById("deq-qs-add-modal"),
  addHeading: () => document.getElementById("deq-qs-new-heading"),
  addCtype: () => document.getElementById("deq-qs-new-ctype"),   // hidden input
  addBuilder: () => document.getElementById("deq-qs-builder"),
  btnAddItem: () => document.getElementById("btn-deq-qs-add-item"),
  btnAddSave: () => document.getElementById("btn-deq-qs-add-save"),
  btnAddCancel: () => document.getElementById("btn-deq-qs-add-cancel"),
  btnAddCancel2: () => document.getElementById("btn-deq-qs-add-cancel2"),
  addFeedback: () => document.getElementById("deq-qs-add-feedback"),
  // Edit modal
  editModal: () => document.getElementById("deq-qs-edit-modal"),
  editHeading: () => document.getElementById("deq-qs-edit-heading"),
  editCtype: () => document.getElementById("deq-qs-edit-ctype"),  // hidden input
  editBuilder: () => document.getElementById("deq-qs-edit-builder"),
  btnEditAddItem: () => document.getElementById("btn-deq-qs-edit-add-item"),
  btnEditSave: () => document.getElementById("btn-deq-qs-edit-save"),
  btnEditCancel: () => document.getElementById("btn-deq-qs-edit-cancel"),
  btnEditCancel2: () => document.getElementById("btn-deq-qs-edit-cancel2"),
  editFeedback: () => document.getElementById("deq-qs-edit-feedback"),
  editId: () => document.getElementById("deq-qs-edit-id"),
};

// ── DEQ Sync state ────────────────────────────────────────────────────────
function setDeqSync(id, syncState) {
  state.deqSync[id] = syncState;
}
function getDeqSync(id) {
  return state.deqSync[id] || "idle";
}

// ── Load all DEQ data ─────────────────────────────────────────────────────
async function loadDeqData() {
  try {
    const [pipelineResp, dashResp, clientsResp] = await Promise.all([
      api("/api/deq/pipeline"),
      api("/api/deq/dashboard"),
      api("/api/deq/bhc-clients"),
    ]);
    const [pipelineRes, dashRes, clientsRes] = await Promise.all([
      pipelineResp.json(),
      dashResp.json(),
      clientsResp.json(),
    ]);
    state.deqRecords = pipelineRes.records || [];
    state.deqFiltered = [...state.deqRecords];
    renderDeqStats(dashRes);
    renderDeqPipeline(state.deqFiltered);
    populateDeqBhcSelector(clientsRes.clients || []);
    state.deqBhcClients = clientsRes.clients || [];
    updateDeqCount();

    // Load studio if admin
    if (state.session?.is_admin) {
      deqEl.studioLocked()?.classList.add("hidden");
      deqEl.studioContent()?.classList.remove("hidden");
      loadDeqSections();
    } else {
      deqEl.studioLocked()?.classList.remove("hidden");
      deqEl.studioContent()?.classList.add("hidden");
    }
  } catch (err) {
    toast("Failed to load DEQ data: " + err.message, "error");
  }
}

// ── Stats ─────────────────────────────────────────────────────────────────
function renderDeqStats(summary) {
  const fmt = (v) => "₹ " + Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
  const el = deqEl;
  if (el.mTotal()) el.mTotal().textContent = summary.total ?? 0;
  if (el.mConverted()) el.mConverted().textContent = summary.converted ?? 0;
  if (el.mRevenue()) el.mRevenue().textContent = fmt(summary.total_revenue);
  if (el.mPaid()) el.mPaid().textContent = fmt(summary.converted_revenue);
}

function updateDeqCount() {
  const c = deqEl.count();
  if (c) c.textContent = state.deqFiltered.length;
}

// ── BHC Client Selector ───────────────────────────────────────────────────
function populateDeqBhcSelector(clients) {
  const sel = deqEl.bhcSelect();
  if (!sel) return;
  sel.innerHTML = '<option value="">— Select Linked BHC Record (optional) —</option>';
  clients.forEach((c) => {
    const label = [c.bhc_reference_number, c.client_name, c.phone].filter(Boolean).join(" | ");
    const opt = document.createElement("option");
    opt.value = c.id || "";
    opt.dataset.record = JSON.stringify(c);
    opt.textContent = label;
    sel.appendChild(opt);
  });
}

function onDeqBhcSelect() {
  const sel = deqEl.bhcSelect();
  if (!sel || !sel.value) return;
  const opt = sel.options[sel.selectedIndex];
  try {
    const rec = JSON.parse(opt.dataset.record || "{}");
    if (deqEl.clientName() && rec.client_name) deqEl.clientName().value = rec.client_name;
    if (deqEl.phone() && rec.phone) deqEl.phone().value = rec.phone || "";
    if (deqEl.propertyType() && rec.property_type) deqEl.propertyType().value = rec.property_type || "";
    if (deqEl.area() && rec.area) deqEl.area().value = rec.area || "";
  } catch (_) {}
}

// ── Create DEQ ────────────────────────────────────────────────────────────
async function onCreateDeq() {
  const fb = deqEl.formFeedback();
  const clientName = (deqEl.clientName()?.value || "").trim();
  const amount = parseFloat(deqEl.amount()?.value || "0");
  if (!clientName) {
    if (fb) { fb.textContent = "Client name is required."; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
    return;
  }
  if (isNaN(amount) || amount < 0) {
    if (fb) { fb.textContent = "Enter a valid DEQ amount."; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
    return;
  }

  const sel = deqEl.bhcSelect();
  const selOpt = sel && sel.value ? sel.options[sel.selectedIndex] : null;
  let bhcEnquiryId = "";
  let bhcRefNumber = "";
  if (selOpt) {
    try {
      const rec = JSON.parse(selOpt.dataset.record || "{}");
      bhcEnquiryId = rec.id || "";
      bhcRefNumber = rec.bhc_reference_number || "";
    } catch (_) {}
  }

  const payload = {
    bhc_enquiry_id: bhcEnquiryId,
    bhc_ref_number: bhcRefNumber,
    client_name: clientName,
    phone: (deqEl.phone()?.value || "").trim(),
    property_type: (deqEl.propertyType()?.value || "").trim(),
    area: parseFloat(deqEl.area()?.value) || null,
    issue_description: (deqEl.issueDescription()?.value || "").trim(),
    examination_type: deqEl.examType()?.value || "Structural",
    deq_quoted_amount: amount,
  };

  const btn = deqEl.btnCreate();
  if (btn) btn.disabled = true;
  try {
    const resp = await api("/api/deq/pipeline", { method: "POST", body: JSON.stringify(payload), headers: { "Content-Type": "application/json" } });
    const res = await resp.json();
    const ref = res.record?.deq_reference_number || "Created";
    const refDiv = deqEl.createdRef();
    if (refDiv) { refDiv.textContent = "✔ DEQ Created: " + ref; refDiv.classList.remove("hidden"); }
    if (fb) fb.classList.add("hidden");
    // Clear form
    ["clientName","phone","propertyType","area","amount","issueDescription"].forEach((k) => { if (deqEl[k]()) deqEl[k]().value = ""; });
    if (deqEl.bhcSelect()) deqEl.bhcSelect().value = "";
    toast("DEQ Quotation created: " + ref, "success");
    loadDeqData();
  } catch (err) {
    if (fb) { fb.textContent = err.message; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
    toast(err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── DEQ Pipeline Render ───────────────────────────────────────────────────
function renderDeqPipeline(rows) {
  const tbody = deqEl.body();
  if (!tbody) return;
  if (!rows || rows.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" class="muted">No DEQ records found.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map((row) => {
    const sid = escHtml(row.id);
    const syncState = getDeqSync(row.id);
    const syncPill = syncState === "saving"
      ? '<span class="sync-pill saving">Saving…</span>'
      : syncState === "saved"
        ? '<span class="sync-pill saved">Saved ✓</span>'
        : syncState === "error"
          ? '<span class="sync-pill error">Error</span>'
          : '<span class="sync-pill">—</span>';
    return `<tr data-id="${sid}">
      <td><span class="mono text-sm">${escHtml(row.deq_reference_number || "—")}</span></td>
      <td><span class="mono text-sm">${escHtml(row.bhc_ref_number || "—")}</span></td>
      <td>${escHtml(row.client_name || "")}</td>
      <td>${escHtml(row.examination_type || "")}</td>
      <td>₹ ${Number(row.deq_quoted_amount || 0).toLocaleString("en-IN", {maximumFractionDigits:0})}</td>
      <td>
        <select class="filter-select filter-select--sm deq-status-sel" data-id="${sid}">
          ${["Quoted","Converted","Dropped"].map((s) => `<option value="${s}"${row.status===s?" selected":""}>${s}</option>`).join("")}
        </select>
      </td>
      <td>
        <select class="filter-select filter-select--sm deq-payment-sel" data-id="${sid}">
          ${["Pending","Paid"].map((p) => `<option value="${p}"${row.payment_status===p?" selected":""}>${p}</option>`).join("")}
        </select>
      </td>
      <td><input type="text" class="search-input search-input--sm deq-remarks-inp" data-id="${sid}" value="${escHtml(row.remarks||"")}" placeholder="Remarks" /></td>
      <td>${syncPill}</td>
      <td class="actions-cell">
        <button class="btn btn-sm btn-primary deq-save-btn" data-id="${sid}" title="Save changes">Save</button>
        <button class="btn btn-sm btn-outline deq-pdf-btn" data-id="${sid}" title="Download PDF">PDF</button>
        ${state.session?.is_admin ? `<button class="btn btn-sm btn-danger deq-del-btn" data-id="${sid}" title="Delete">Del</button>` : ""}
      </td>
    </tr>`;
  }).join("");

  // Bind events
  tbody.querySelectorAll(".deq-save-btn").forEach((btn) => {
    btn.addEventListener("click", () => onDeqSave(btn.dataset.id));
  });
  tbody.querySelectorAll(".deq-pdf-btn").forEach((btn) => {
    btn.addEventListener("click", () => onDeqDownloadPdf(btn.dataset.id));
  });
  tbody.querySelectorAll(".deq-del-btn").forEach((btn) => {
    btn.addEventListener("click", () => onDeqDelete(btn.dataset.id));
  });
}

// ── Apply Filters ─────────────────────────────────────────────────────────
function applyDeqFilters() {
  const q = (deqEl.search()?.value || "").toLowerCase();
  const status = deqEl.statusFilter()?.value || "all";
  state.deqFiltered = state.deqRecords.filter((r) => {
    const matchStatus = status === "all" || r.status === status;
    const matchSearch = !q || [r.deq_reference_number, r.bhc_ref_number, r.client_name, r.examination_type]
      .some((v) => v && v.toLowerCase().includes(q));
    return matchStatus && matchSearch;
  });
  renderDeqPipeline(state.deqFiltered);
  updateDeqCount();
}

// ── Save DEQ Record ───────────────────────────────────────────────────────
async function onDeqSave(id) {
  const row = document.querySelector(`tr[data-id="${id}"]`);
  if (!row) return;
  const status = row.querySelector(".deq-status-sel")?.value;
  const paymentStatus = row.querySelector(".deq-payment-sel")?.value;
  const remarks = row.querySelector(".deq-remarks-inp")?.value || "";

  setDeqSync(id, "saving");
  renderDeqPipeline(state.deqFiltered);

  try {
    await api(`/api/deq/pipeline/${id}`, {
      method: "PUT",
      body: JSON.stringify({ status, payment_status: paymentStatus, remarks }),
      headers: { "Content-Type": "application/json" },
    });
    setDeqSync(id, "saved");
    // Update local state
    const idx = state.deqRecords.findIndex((r) => r.id === id);
    if (idx >= 0) { state.deqRecords[idx].status = status; state.deqRecords[idx].payment_status = paymentStatus; state.deqRecords[idx].remarks = remarks; }
    applyDeqFilters();
    toast("DEQ record saved", "success");
  } catch (err) {
    setDeqSync(id, "error");
    applyDeqFilters();
    toast(err.message, "error");
  }
}

// ── Download DEQ PDF ──────────────────────────────────────────────────────
async function onDeqDownloadPdf(id) {
  const btn = document.querySelector(`.deq-pdf-btn[data-id="${id}"]`);
  if (btn) btn.disabled = true;
  try {
    const resp = await fetch(`/api/deq/download/pdf/${id}`, {
      method: "POST",
      credentials: "include",
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "PDF generation failed" }));
      throw new Error(err.detail || "PDF error");
    }
    const blob = await resp.blob();
    const cd = resp.headers.get("content-disposition") || "";
    const match = cd.match(/filename="(.+)"/);
    const filename = match ? match[1] : `DEQ_${id}.pdf`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast("DEQ PDF downloaded", "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── Delete DEQ ────────────────────────────────────────────────────────────
async function onDeqDelete(id) {
  const confirmed = await confirmAction({ title: "Delete DEQ Record", message: "This action cannot be undone. Delete this DEQ record?", confirmText: "Delete", type: "danger" });
  if (!confirmed) return;
  try {
    await api(`/api/deq/pipeline/${id}`, { method: "DELETE" });
    state.deqRecords = state.deqRecords.filter((r) => r.id !== id);
    applyDeqFilters();
    toast("DEQ record deleted", "success");
    loadDeqData(); // refresh stats
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Export DEQ Excel ──────────────────────────────────────────────────────
async function onDeqExport() {
  const btn = deqEl.btnExport();
  if (btn) btn.disabled = true;
  try {
    const resp = await fetch("/api/deq/export", { credentials: "include" });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Export failed" }));
      throw new Error(err.detail || "Export failed");
    }
    const blob = await resp.blob();
    const cd = resp.headers.get("content-disposition") || "";
    const match = cd.match(/filename="(.+)"/);
    const filename = match ? match[1] : "DEQ_Pipeline.xlsx";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast("DEQ pipeline exported", "success");
  } catch (err) {
    toast(err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ── DEQ Sections Admin ────────────────────────────────────────────────────
async function loadDeqSections() {
  try {
    const resp = await api("/api/deq/admin/sections");
    const res = await resp.json();
    state.deqSections = res.deq_sections || [];
    renderDeqAdminSections(state.deqSections);
  } catch (err) {
    toast("Failed to load DEQ sections: " + err.message, "error");
  }
}

function renderDeqAdminSections(sections) {
  const container = deqEl.qsList();
  if (!container) return;
  if (!sections || sections.length === 0) {
    container.innerHTML = '<p class="muted" style="padding:12px 0">No sections configured. Click &quot;+ Add New DEQ Section&quot; to create one.</p>';
    return;
  }
  container.innerHTML = sections.map((sec, idx) => {
    const typeLabel = { list: "Numbered List", paragraph: "Paragraphs", table: "Table", dynamic: "Dynamic" }[sec.content_type] || sec.content_type;
    const systemBadge = sec.is_system
      ? '<span class="qs-badge qs-badge--system">System</span>'
      : '<span class="qs-badge qs-badge--custom">Custom</span>';
    const hiddenBadge = !sec.is_visible ? '<span class="qs-badge qs-badge--hidden">Hidden</span>' : "";
    const isDynamic = sec.content_type === "dynamic";
    return `
      <div class="qs-item" data-deq-id="${sec.id}" data-deq-idx="${idx}" draggable="true">
        <div class="qs-drag-handle" title="Drag to reorder">&#9776;</div>
        <div class="qs-item-info">
          <div class="qs-item-heading">${escHtml(sec.heading)}</div>
          <div class="qs-item-meta">${systemBadge}${hiddenBadge} ${escHtml(typeLabel)}</div>
        </div>
        <label class="qs-toggle" title="${sec.is_visible ? "Visible \u2014 click to hide" : "Hidden \u2014 click to show"}">
          <input type="checkbox" ${sec.is_visible ? "checked" : ""} data-deq-toggle="${sec.id}" />
          <span class="qs-toggle-slider"></span>
        </label>
        <div class="qs-item-actions">
          ${!isDynamic ? `<button class="btn btn-outline btn-sm" data-deq-edit="${sec.id}">Edit</button>` : ""}
          ${!sec.is_system ? `<button class="btn btn-outline btn-sm" style="color:#dc2626" data-deq-delete="${sec.id}">Delete</button>` : ""}
        </div>
      </div>
    `;
  }).join("");

  container.querySelectorAll(".qs-item[draggable='true']").forEach((item) => {
    item.addEventListener("dragstart", _onDeqQsDragStart);
    item.addEventListener("dragover", _onDeqQsDragOver);
    item.addEventListener("dragleave", _onDeqQsDragLeave);
    item.addEventListener("drop", _onDeqQsDrop);
    item.addEventListener("dragend", _onDeqQsDragEnd);
  });
  container.querySelectorAll("[data-deq-toggle]").forEach((toggle) => {
    toggle.addEventListener("change", _onDeqQsToggle);
  });
  container.querySelectorAll("[data-deq-edit]").forEach((btn) => {
    btn.addEventListener("click", () => openDeqQsEditModal(parseInt(btn.dataset.deqEdit)));
  });
  container.querySelectorAll("[data-deq-delete]").forEach((btn) => {
    btn.addEventListener("click", () => onDeqQsDelete(parseInt(btn.dataset.deqDelete)));
  });
}

// ── DEQ Drag & Drop ───────────────────────────────────────────────────────
let _deqQsDragSrcId = null;

function _onDeqQsDragStart(e) {
  _deqQsDragSrcId = parseInt(e.currentTarget.dataset.deqId);
  e.currentTarget.classList.add("qs-dragging");
  e.dataTransfer.effectAllowed = "move";
}
function _onDeqQsDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  e.currentTarget.classList.add("qs-drag-over");
}
function _onDeqQsDragLeave(e) {
  e.currentTarget.classList.remove("qs-drag-over");
}
function _onDeqQsDrop(e) {
  e.preventDefault();
  e.currentTarget.classList.remove("qs-drag-over");
  const targetId = parseInt(e.currentTarget.dataset.deqId);
  if (!_deqQsDragSrcId || _deqQsDragSrcId === targetId) return;
  const srcIdx = state.deqSections.findIndex((s) => s.id === _deqQsDragSrcId);
  const tgtIdx = state.deqSections.findIndex((s) => s.id === targetId);
  if (srcIdx < 0 || tgtIdx < 0) return;
  const [moved] = state.deqSections.splice(srcIdx, 1);
  state.deqSections.splice(tgtIdx, 0, moved);
  renderDeqAdminSections(state.deqSections);
  api("/api/deq/admin/sections/reorder", {
    method: "PUT",
    body: JSON.stringify({ ordered_ids: state.deqSections.map((s) => s.id) }),
    headers: { "Content-Type": "application/json" },
  }).catch((err) => { toast("Failed to save order: " + err.message, "error"); loadDeqSections(); });
}
function _onDeqQsDragEnd(e) {
  e.currentTarget.classList.remove("qs-dragging");
  _deqQsDragSrcId = null;
}
function _onDeqQsToggle(e) {
  const id = parseInt(e.currentTarget.dataset.deqToggle);
  const isNowVisible = e.currentTarget.checked;
  api(`/api/deq/admin/sections/${id}`, {
    method: "PUT",
    body: JSON.stringify({ is_visible: isNowVisible }),
    headers: { "Content-Type": "application/json" },
  }).then(() => loadDeqSections())
    .catch((err) => { toast(err.message, "error"); e.currentTarget.checked = !isNowVisible; });
}

async function onDeqQsDelete(id) {
  const confirmed = await confirmAction({ title: "Delete DEQ Section", message: "Delete this section? This cannot be undone.", confirmText: "Delete", type: "danger" });
  if (!confirmed) return;
  try {
    await api(`/api/deq/admin/sections/${id}`, { method: "DELETE" });
    toast("DEQ section deleted", "success");
    loadDeqSections();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── DEQ Studio Modals ─────────────────────────────────────────────────────
let _deqBuilderItems = [];
let _deqEditBuilderItems = [];

function openDeqQsAddModal() {
  _deqBuilderItems = [];
  if (deqEl.addHeading()) deqEl.addHeading().value = "";
  const ctypeInput = deqEl.addCtype();
  if (ctypeInput) ctypeInput.value = "list";
  document.querySelectorAll("#deq-qs-add-modal .qs-type-card").forEach((c) =>
    c.classList.toggle("qs-type-card--active", c.dataset.deqTypeAdd === "list")
  );
  if (deqEl.addBuilder()) deqEl.addBuilder().innerHTML = "";
  if (deqEl.addFeedback()) deqEl.addFeedback().classList.add("hidden");
  deqEl.addModal()?.classList.remove("hidden");
}

function closeDeqQsAddModal() {
  deqEl.addModal()?.classList.add("hidden");
}

function openDeqQsEditModal(id) {
  const sec = state.deqSections.find((s) => s.id === id);
  if (!sec) return;
  if (deqEl.editId()) deqEl.editId().value = id;
  if (deqEl.editHeading()) deqEl.editHeading().value = sec.heading;
  const ctype = sec.content_type || "list";
  const ctypeInput = deqEl.editCtype();
  if (ctypeInput) ctypeInput.value = ctype;
  document.querySelectorAll("#deq-qs-edit-modal .qs-type-card").forEach((c) =>
    c.classList.toggle("qs-type-card--active", c.dataset.deqTypeEdit === ctype)
  );
  _deqEditBuilderItems = Array.isArray(sec.content) ? JSON.parse(JSON.stringify(sec.content)) : [];
  renderDeqEditBuilder();
  if (deqEl.editFeedback()) deqEl.editFeedback().classList.add("hidden");
  deqEl.editModal()?.classList.remove("hidden");
}

function closeDeqQsEditModal() {
  deqEl.editModal()?.classList.add("hidden");
}

function renderDeqAddBuilder() {
  const container = deqEl.addBuilder();
  if (!container) return;
  container.innerHTML = _deqBuilderItems.map((item, idx) =>
    `<div class="qs-builder-item">
      <div class="qs-builder-item-num">${idx + 1}</div>
      <input type="text" class="search-input" value="${escHtml(String(item))}" data-idx="${idx}" placeholder="Item ${idx + 1}" />
      <button class="qs-builder-remove deq-add-rm" data-idx="${idx}" title="Remove">&times;</button>
    </div>`
  ).join("");
  container.querySelectorAll(".deq-add-rm").forEach((btn) => {
    btn.addEventListener("click", () => { _deqBuilderItems.splice(parseInt(btn.dataset.idx), 1); renderDeqAddBuilder(); });
  });
  container.querySelectorAll("input").forEach((inp) => {
    inp.addEventListener("input", () => { _deqBuilderItems[parseInt(inp.dataset.idx)] = inp.value; });
  });
}

function renderDeqEditBuilder() {
  const container = deqEl.editBuilder();
  if (!container) return;
  container.innerHTML = _deqEditBuilderItems.map((item, idx) =>
    `<div class="qs-builder-item">
      <div class="qs-builder-item-num">${idx + 1}</div>
      <input type="text" class="search-input" value="${escHtml(String(item))}" data-idx="${idx}" placeholder="Item ${idx + 1}" />
      <button class="qs-builder-remove deq-edit-rm" data-idx="${idx}" title="Remove">&times;</button>
    </div>`
  ).join("");
  container.querySelectorAll(".deq-edit-rm").forEach((btn) => {
    btn.addEventListener("click", () => { _deqEditBuilderItems.splice(parseInt(btn.dataset.idx), 1); renderDeqEditBuilder(); });
  });
  container.querySelectorAll("input").forEach((inp) => {
    inp.addEventListener("input", () => { _deqEditBuilderItems[parseInt(inp.dataset.idx)] = inp.value; });
  });
}

async function onDeqQsAddSave() {
  const heading = (deqEl.addHeading()?.value || "").trim();
  const fb = deqEl.addFeedback();
  if (!heading) {
    if (fb) { fb.textContent = "Heading is required."; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
    return;
  }
  try {
    await api("/api/deq/admin/sections", {
      method: "POST",
      body: JSON.stringify({ heading, content_type: deqEl.addCtype()?.value || "list", content: _deqBuilderItems.filter(Boolean) }),
      headers: { "Content-Type": "application/json" },
    });
    closeDeqQsAddModal();
    toast("DEQ section added", "success");
    loadDeqSections();
  } catch (err) {
    if (fb) { fb.textContent = err.message; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
  }
}

async function onDeqQsEditSave() {
  const id = parseInt(deqEl.editId()?.value);
  const heading = (deqEl.editHeading()?.value || "").trim();
  const fb = deqEl.editFeedback();
  if (!heading) {
    if (fb) { fb.textContent = "Heading is required."; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
    return;
  }
  try {
    await api(`/api/deq/admin/sections/${id}`, {
      method: "PUT",
      body: JSON.stringify({ heading, content_type: deqEl.editCtype()?.value || "list", content: _deqEditBuilderItems.filter(Boolean) }),
      headers: { "Content-Type": "application/json" },
    });
    closeDeqQsEditModal();
    toast("DEQ section updated", "success");
    loadDeqSections();
  } catch (err) {
    if (fb) { fb.textContent = err.message; fb.className = "feedback feedback-error"; fb.classList.remove("hidden"); }
  }
}

// ── DEQ Event Binding ─────────────────────────────────────────────────────
function bindDeqEvents() {
  deqEl.bhcSelect()?.addEventListener("change", onDeqBhcSelect);
  deqEl.btnCreate()?.addEventListener("click", onCreateDeq);
  deqEl.btnExport()?.addEventListener("click", onDeqExport);
  deqEl.search()?.addEventListener("input", applyDeqFilters);
  deqEl.statusFilter()?.addEventListener("change", applyDeqFilters);
  deqEl.btnAddSection()?.addEventListener("click", openDeqQsAddModal);
  // Add modal
  deqEl.btnAddCancel()?.addEventListener("click", closeDeqQsAddModal);
  deqEl.btnAddCancel2()?.addEventListener("click", closeDeqQsAddModal);
  deqEl.btnAddSave()?.addEventListener("click", onDeqQsAddSave);
  deqEl.btnAddItem()?.addEventListener("click", () => { _deqBuilderItems.push(""); renderDeqAddBuilder(); });
  // Add modal type cards
  document.querySelectorAll("#deq-qs-add-modal .qs-type-card").forEach((card) => {
    card.addEventListener("click", () => {
      const ctype = card.dataset.deqTypeAdd;
      document.querySelectorAll("#deq-qs-add-modal .qs-type-card").forEach((c) => c.classList.remove("qs-type-card--active"));
      card.classList.add("qs-type-card--active");
      const inp = document.getElementById("deq-qs-new-ctype");
      if (inp) inp.value = ctype;
    });
  });
  // Edit modal
  deqEl.btnEditCancel()?.addEventListener("click", closeDeqQsEditModal);
  deqEl.btnEditCancel2()?.addEventListener("click", closeDeqQsEditModal);
  deqEl.btnEditSave()?.addEventListener("click", onDeqQsEditSave);
  deqEl.btnEditAddItem()?.addEventListener("click", () => { _deqEditBuilderItems.push(""); renderDeqEditBuilder(); });
  // Edit modal type cards
  document.querySelectorAll("#deq-qs-edit-modal .qs-type-card").forEach((card) => {
    card.addEventListener("click", () => {
      const ctype = card.dataset.deqTypeEdit;
      document.querySelectorAll("#deq-qs-edit-modal .qs-type-card").forEach((c) => c.classList.remove("qs-type-card--active"));
      card.classList.add("qs-type-card--active");
      const inp = document.getElementById("deq-qs-edit-ctype");
      if (inp) inp.value = ctype;
    });
  });
}

// Initialise DEQ events after DOM ready
document.addEventListener("DOMContentLoaded", bindDeqEvents);
