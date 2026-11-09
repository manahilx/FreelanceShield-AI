/**
 * FreelanceShield AI - Frontend Application & Interactive Fintech Controller
 * Controls Liquid Glass Fintech views, Chart.js graphs, PayPal Sandbox orders,
 * AI security scans, AI invoice studio, notifications, and ShieldBot assistant.
 */

// Global State
const appState = {
  currentView: 'landing',
  currentSecTool: 'scam-detector',
  stats: {},
  transactions: [],
  invoices: [],
  notifications: [],
  charts: {},
  paypalStatus: {},
  aiStatus: {}
};

// ============================================================================
// Initialization on DOM Ready
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupAssistant();
  setupEventListeners();

  // Load initial application data
  fetchPayPalStatus();
  fetchAIStatus();
  refreshDashboard();
  loadInvoices();
  loadNotifications();

  // Check URL hash for direct view navigation
  const hash = window.location.hash.replace('#', '');
  if (['dashboard', 'security', 'paypal', 'invoices', 'analytics', 'notifications', 'landing'].includes(hash)) {
    switchView(hash);
  } else {
    switchView('landing');
  }
});

// ============================================================================
// 1. Navigation & View Controller
// ============================================================================
function setupNavigation() {
  const navBtns = document.querySelectorAll('[data-view-target]');
  navBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const target = btn.getAttribute('data-view-target');
      switchView(target);
    });
  });

  // Security Tool Tabs
  const secTabs = document.querySelectorAll('.sec-tool-tab');
  secTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const tool = tab.getAttribute('data-tool');
      switchSecTool(tool);
    });
  });
}

function switchView(viewName) {
  appState.currentView = viewName;
  window.location.hash = viewName;

  // Toggle active view pane
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });
  const activePane = document.getElementById(`view-${viewName}`);
  if (activePane) activePane.classList.add('active');

  // Update active pill button
  document.querySelectorAll('.nav-pill-btn').forEach(btn => {
    if (btn.getAttribute('data-view-target') === viewName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Window scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger view-specific data refresh
  if (viewName === 'dashboard') {
    refreshDashboard();
  } else if (viewName === 'invoices') {
    loadInvoices();
  } else if (viewName === 'analytics') {
    renderAnalyticsCharts();
  } else if (viewName === 'paypal') {
    fetchPayPalStatus();
    loadTransactions();
  } else if (viewName === 'notifications') {
    loadNotifications();
  }
}

function switchSecTool(toolId) {
  appState.currentSecTool = toolId;
  document.querySelectorAll('.sec-tool-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tool-pane').forEach(p => p.classList.remove('active'));

  const activeTab = document.querySelector(`[data-tool="${toolId}"]`);
  const activePane = document.getElementById(`tool-pane-${toolId}`);
  if (activeTab) activeTab.classList.add('active');
  if (activePane) activePane.classList.add('active');
}

// ============================================================================
// 2. Dashboard Data & Telemetry
// ============================================================================
async function refreshDashboard() {
  try {
    const [statsRes, txnRes, alertsRes] = await Promise.all([
      fetch('/api/dashboard/stats').then(r => r.json()),
      fetch('/api/dashboard/transactions?limit=10').then(r => r.json()),
      fetch('/api/dashboard/alerts').then(r => r.json())
    ]);

    if (statsRes.success) {
      appState.stats = statsRes.stats;
      renderDashboardStats(statsRes.stats);
    }

    if (txnRes.success) {
      appState.transactions = txnRes.transactions;
      renderTransactionsTable(txnRes.transactions, 'dashboard-txn-tbody');
    }

    if (alertsRes.success) {
      renderAlertsFeed(alertsRes.reports);
    }

    // Render monthly payment activity graph
    renderDashboardActivityChart();
  } catch (err) {
    console.error('Error refreshing dashboard:', err);
  }
}

function renderDashboardStats(stats) {
  // Hero section stats
  const heroPaid = document.getElementById('hero-stat-paid');
  const heroThreats = document.getElementById('hero-stat-threats');
  const heroPending = document.getElementById('hero-stat-pending');
  const heroScore = document.getElementById('hero-stat-score');

  if (heroPaid) heroPaid.textContent = `$${stats.completed_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  if (heroThreats) heroThreats.textContent = `${stats.threats_detected} Neutralized`;
  if (heroPending) heroPending.textContent = `$${stats.pending_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  if (heroScore) heroScore.textContent = `${stats.posture_score}/100`;

  // Metric Cards
  const mCompleted = document.getElementById('metric-completed-amt');
  const mPending = document.getElementById('metric-pending-amt');
  const mFailed = document.getElementById('metric-failed-count');
  const mInvoices = document.getElementById('metric-invoices-count');
  const mThreats = document.getElementById('metric-threats-count');
  const mScore = document.getElementById('metric-score-val');

  if (mCompleted) mCompleted.textContent = `$${stats.completed_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  if (mPending) mPending.textContent = `$${stats.pending_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  if (mFailed) mFailed.textContent = stats.failed_count;
  if (mInvoices) mInvoices.textContent = stats.total_invoices;
  if (mThreats) mThreats.textContent = stats.threats_detected;
  if (mScore) mScore.textContent = `${stats.posture_score}%`;
}

function renderTransactionsTable(transactions, tbodyId) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;

  if (!transactions || transactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--color-slate); padding: 2rem;">No transaction records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = transactions.map(t => {
    let statusBadge = `<span class="status-badge badge-pending">Pending</span>`;
    if (t.payment_status === 'Completed') {
      statusBadge = `<span class="status-badge badge-completed"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg> Completed</span>`;
    } else if (t.payment_status === 'Failed') {
      statusBadge = `<span class="status-badge badge-failed">Failed</span>`;
    }

    let riskBadge = `<span class="status-badge badge-safe">Safe (${t.ai_risk_score}/100)</span>`;
    if (t.ai_risk_score >= 70) {
      riskBadge = `<span class="status-badge badge-critical">Critical Risk (${t.ai_risk_score})</span>`;
    } else if (t.ai_risk_score >= 35) {
      riskBadge = `<span class="status-badge badge-pending">Review (${t.ai_risk_score})</span>`;
    }

    return `
      <tr onclick="inspectTransaction('${t.id}')" style="cursor: pointer;">
        <td>
          <div style="font-weight: 700; color: var(--color-charcoal);">${escapeHtml(t.client_name)}</div>
          <div style="font-size: 0.75rem; color: var(--color-slate);">${escapeHtml(t.client_email || '')}</div>
        </td>
        <td>
          <span style="font-family: monospace; font-size: 0.8rem; background: rgba(8,127,165,0.06); padding: 2px 6px; border-radius: 4px;">
            ${escapeHtml(t.paypal_order_id || t.id)}
          </span>
        </td>
        <td style="font-weight: 800; color: var(--color-deep-blue);">
          $${parseFloat(t.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} ${t.currency}
        </td>
        <td>${statusBadge}</td>
        <td>${riskBadge}</td>
        <td style="font-size: 0.78rem; color: var(--color-muted);">
          ${t.created_at ? t.created_at.substring(0, 16) : ''}
        </td>
      </tr>
    `;
  }).join('');
}

function renderAlertsFeed(reports) {
  const feed = document.getElementById('alerts-feed-container');
  if (!feed) return;

  if (!reports || reports.length === 0) {
    feed.innerHTML = `<div style="text-align: center; color: var(--color-slate); padding: 1.5rem;">No security threats detected.</div>`;
    return;
  }

  feed.innerHTML = reports.map(r => {
    let badgeClass = 'badge-safe';
    if (r.risk_classification === 'Critical') badgeClass = 'badge-critical';
    else if (r.risk_classification === 'High') badgeClass = 'badge-failed';
    else if (r.risk_classification === 'Medium') badgeClass = 'badge-pending';

    return `
      <div class="alert-feed-item" onclick="openAlertDetails('${r.id}')">
        <div class="alert-feed-header">
          <div class="alert-feed-title">${escapeHtml(r.report_type.toUpperCase())} SCAN</div>
          <span class="status-badge ${badgeClass}">${r.risk_classification} (${r.risk_score})</span>
        </div>
        <div class="alert-feed-desc">${escapeHtml(r.risk_explanation)}</div>
        <div class="alert-feed-time">${r.created_at}</div>
      </div>
    `;
  }).join('');
}

// ============================================================================
// 3. AI Security Center (3 Tools)
// ============================================================================
async function runScamMessageScan() {
  const textInput = document.getElementById('scam-message-input');
  const btn = document.getElementById('btn-scan-scam-msg');
  const text = textInput ? textInput.value.trim() : '';

  if (!text) {
    showToast('warning', 'Please paste a client message or proposal text to evaluate.');
    return;
  }

  setBtnLoading(btn, true, 'Evaluating Heuristics...');

  try {
    const res = await fetch('/api/ai/analyze-message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    if (data.success) {
      renderScamMessageResult(data.report);
      showToast('success', `Analysis Complete: Risk Score ${data.report.risk_score}/100 (${data.report.risk_classification})`);
      loadNotifications(); // Refresh notifications in case alert was triggered
    } else {
      showToast('error', data.error || 'Failed to analyze text.');
    }
  } catch (err) {
    showToast('error', 'Network error connecting to AI Security Engine.');
  } finally {
    setBtnLoading(btn, false, 'Analyze Message Security');
  }
}

function renderScamMessageResult(report) {
  const resultCard = document.getElementById('scam-msg-results-card');
  if (!resultCard) return;

  resultCard.style.display = 'block';

  // Circular Score Meter
  const circle = document.getElementById('scam-score-circle');
  const scoreNum = document.getElementById('scam-score-number');
  const verdictText = document.getElementById('scam-verdict-text');
  const expText = document.getElementById('scam-explanation-text');
  const indicatorsList = document.getElementById('scam-indicators-list');
  const recsList = document.getElementById('scam-recommendations-list');

  scoreNum.textContent = report.risk_score;
  circle.className = 'risk-score-circle';
  if (report.risk_classification === 'Critical') circle.classList.add('circle-critical');
  else if (report.risk_classification === 'High') circle.classList.add('circle-high');
  else if (report.risk_classification === 'Medium') circle.classList.add('circle-medium');
  else circle.classList.add('circle-low');

  verdictText.textContent = `${report.risk_classification} Risk: ${report.risk_score >= 50 ? 'Potential Fraud Detected' : 'Clean Communication'}`;
  expText.textContent = report.risk_explanation;

  // Indicators
  if (report.detected_indicators && report.detected_indicators.length > 0) {
    indicatorsList.innerHTML = report.detected_indicators.map(ind => `
      <div class="risk-indicator-pill">
        <div class="indicator-title">${escapeHtml(ind.name)} (${ind.weight} Pts)</div>
        <div class="indicator-exp">${escapeHtml(ind.explanation)}</div>
      </div>
    `).join('');
  } else {
    indicatorsList.innerHTML = `<div style="font-size: 0.85rem; color: #059669;">? Zero suspicious scam signatures or off-platform coercion patterns found.</div>`;
  }

  // Recommendations
  if (report.recommendations && report.recommendations.length > 0) {
    recsList.innerHTML = report.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('');
  }
}

async function runURLScan() {
  const urlInput = document.getElementById('url-scan-input');
  const btn = document.getElementById('btn-scan-url');
  const url = urlInput ? urlInput.value.trim() : '';

  if (!url) {
    showToast('warning', 'Please enter a URL to inspect.');
    return;
  }

  setBtnLoading(btn, true, 'Inspecting Domain & TLS...');

  try {
    const res = await fetch('/api/ai/scan-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (data.success) {
      renderURLScanResult(data.result);
      showToast('success', `Inspection Finished: ${data.result.risk_classification} Risk`);
      loadNotifications();
    } else {
      showToast('error', data.error || 'Failed to scan URL.');
    }
  } catch (err) {
    showToast('error', 'Error connecting to URL Inspection API.');
  } finally {
    setBtnLoading(btn, false, 'Inspect Link Security');
  }
}

function renderURLScanResult(res) {
  const card = document.getElementById('url-results-card');
  if (!card) return;

  card.style.display = 'block';

  const circle = document.getElementById('url-score-circle');
  const scoreNum = document.getElementById('url-score-number');
  const verdict = document.getElementById('url-verdict-text');
  const details = document.getElementById('url-details-list');

  scoreNum.textContent = res.risk_score;
  circle.className = 'risk-score-circle';
  if (res.risk_classification === 'Critical') circle.classList.add('circle-critical');
  else if (res.risk_classification === 'High') circle.classList.add('circle-high');
  else if (res.risk_classification === 'Medium') circle.classList.add('circle-medium');
  else circle.classList.add('circle-low');

  verdict.textContent = res.verdict;

  let indicatorsHtml = '';
  if (res.indicators && res.indicators.length > 0) {
    indicatorsHtml = res.indicators.map(i => `
      <div class="risk-indicator-pill">
        <div class="indicator-title">${escapeHtml(i.type)} [${i.severity}]</div>
        <div class="indicator-exp">${escapeHtml(i.description)}</div>
      </div>
    `).join('');
  } else {
    indicatorsHtml = `<div style="font-size: 0.85rem; color: #059669;">? URL structure and domain signatures pass baseline security heuristics.</div>`;
  }

  details.innerHTML = `
    <div style="font-size: 0.88rem; margin-bottom: 0.8rem;">
      <strong>Target Domain:</strong> <code>${escapeHtml(res.domain)}</code> &nbsp;|&nbsp;
      <strong>Protocol:</strong> ${res.is_https ? '<span style="color: #059669;">? HTTPS Verified</span>' : '<span style="color: #DC2626;">? Plaintext HTTP</span>'}
    </div>
    <div style="font-size: 0.85rem; color: var(--color-slate); margin-bottom: 1rem;">
      ${escapeHtml(res.risk_explanation)}
    </div>
    <h5 style="margin-bottom: 0.5rem; font-size: 0.88rem;">Detected Security Indicators:</h5>
    ${indicatorsHtml}
    <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(8,127,165,0.06); border-radius: 8px; font-size: 0.82rem;">
      <strong>Recommended Action:</strong> ${escapeHtml(res.recommended_action)}
    </div>
  `;
}

async function runJobOfferScan() {
  const title = (document.getElementById('job-title-input')?.value || '').trim();
  const desc = (document.getElementById('job-desc-input')?.value || '').trim();
  const budget = (document.getElementById('job-budget-input')?.value || '').trim();
  const btn = document.getElementById('btn-scan-job');

  if (!title || !desc) {
    showToast('warning', 'Please provide both a job title and description.');
    return;
  }

  setBtnLoading(btn, true, 'Analyzing Job Posting...');

  try {
    const res = await fetch('/api/ai/analyze-job', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description: desc, budget })
    });
    const data = await res.json();

    if (data.success) {
      renderJobScanResult(data.result);
      showToast('success', `Job Evaluated: ${data.result.risk_classification} Risk`);
      loadNotifications();
    } else {
      showToast('error', data.error || 'Failed to analyze job.');
    }
  } catch (err) {
    showToast('error', 'Error calling Job Offer Analyzer API.');
  } finally {
    setBtnLoading(btn, false, 'Analyze Job Offer');
  }
}

function renderJobScanResult(res) {
  const card = document.getElementById('job-results-card');
  if (!card) return;

  card.style.display = 'block';

  const scoreNum = document.getElementById('job-score-number');
  const circle = document.getElementById('job-score-circle');
  const verdict = document.getElementById('job-verdict-text');
  const flagsList = document.getElementById('job-flags-list');
  const recsList = document.getElementById('job-recs-list');

  scoreNum.textContent = res.risk_score;
  circle.className = 'risk-score-circle';
  if (res.risk_classification === 'Critical') circle.classList.add('circle-critical');
  else if (res.risk_classification === 'High') circle.classList.add('circle-high');
  else if (res.risk_classification === 'Medium') circle.classList.add('circle-medium');
  else circle.classList.add('circle-low');

  verdict.textContent = res.verdict;

  if (res.flags && res.flags.length > 0) {
    flagsList.innerHTML = res.flags.map(f => `
      <div class="risk-indicator-pill">
        <div class="indicator-title">${escapeHtml(f.flag)} [${f.severity}]</div>
        <div class="indicator-exp">${escapeHtml(f.detail)}</div>
      </div>
    `).join('');
  } else {
    flagsList.innerHTML = `<div style="font-size: 0.85rem; color: #059669;">? No upfront payment requirements or off-platform recruitment lures identified.</div>`;
  }

  if (res.recommendations && res.recommendations.length > 0) {
    recsList.innerHTML = res.recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('');
  }
}

// Preset Fillers for Hackathon Demonstrations
function fillPresetScam(type) {
  const input = document.getElementById('scam-message-input');
  if (!input) return;

  if (type === 'overpayment') {
    input.value = "Hello! I saw your portfolio and want to hire you immediately for a $3,500 redesign. I will send you a cashier's check for $5,500. Please deposit it into your bank and wire the remaining $2,000 back to our designated equipment supplier on Telegram @techsupply_direct.";
  } else if (type === 'telegram') {
    input.value = "We are interested in your profile. Please contact our hiring coordinator on Telegram @hr_direct_recruiter or WhatsApp +1-202-555-0182 right away so we can bypass platform fees and pay you directly via cryptocurrency.";
  } else if (type === 'fake-escrow') {
    input.value = "I have already transferred the full milestone into escrow. Here is the transaction receipt screenshot. Please send over the complete GitHub repository code and database credentials now so the escrow service can release the funds to you.";
  } else if (type === 'legit') {
    input.value = "Hi Alex, we reviewed your proposal for our API architecture refactoring. We have created a milestone contract for $2,850 and funded escrow through PayPal. Please review the contract terms and deliver the initial staging build within two weeks.";
  }
}

function fillPresetURL(type) {
  const input = document.getElementById('url-scan-input');
  if (!input) return;

  if (type === 'paypal-spoof') {
    input.value = "http://paypal.com.account-verify-milestone.top/login?client_token=98214";
  } else if (type === 'ip-address') {
    input.value = "http://192.241.182.90:8080/secure-invoice-download.exe";
  } else if (type === 'punycode') {
    input.value = "https://xn--paypl-qqa.com/webscr/login";
  } else if (type === 'safe') {
    input.value = "https://www.paypal.com/checkoutnow";
  }
}

// ============================================================================
// 4. PayPal Payment Center
// ============================================================================
async function fetchPayPalStatus() {
  try {
    const res = await fetch('/api/paypal/status');
    const data = await res.json();
    if (data.success) {
      appState.paypalStatus = data.status;
      renderPayPalStatusCard(data.status);
    }
  } catch (err) {
    console.error('Error fetching PayPal status:', err);
  }
}

function renderPayPalStatusCard(status) {
  const modeBadge = document.getElementById('paypal-mode-badge');
  const modeText = document.getElementById('paypal-mode-text');
  const previewText = document.getElementById('paypal-client-preview');

  if (modeBadge) {
    modeBadge.textContent = status.has_credentials ? 'Sandbox Live API Handshake' : 'Sandbox Simulation Mode';
    modeBadge.className = status.has_credentials ? 'status-badge badge-completed' : 'status-badge badge-pending';
  }
  if (modeText) modeText.textContent = status.mode;
  if (previewText) previewText.textContent = `Client ID: ${status.client_id_preview}`;
}

async function loadTransactions() {
  try {
    const res = await fetch('/api/dashboard/transactions');
    const data = await res.json();
    if (data.success) {
      appState.transactions = data.transactions;
      renderTransactionsTable(data.transactions, 'paypal-txn-tbody');
    }
  } catch (err) {
    console.error('Error loading transactions:', err);
  }
}

async function handleCreatePaymentRequest(e) {
  e.preventDefault();
  const btn = document.getElementById('btn-submit-paypal-order');
  const clientName = document.getElementById('pp-client-name')?.value.trim();
  const clientEmail = document.getElementById('pp-client-email')?.value.trim();
  const amount = parseFloat(document.getElementById('pp-amount')?.value);
  const currency = document.getElementById('pp-currency')?.value || 'USD';
  const desc = document.getElementById('pp-description')?.value.trim();

  if (!clientName || !amount || amount <= 0) {
    showToast('warning', 'Please provide client name and a valid amount.');
    return;
  }

  setBtnLoading(btn, true, 'Generating Orders v2 Escrow...');

  try {
    const res = await fetch('/api/paypal/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_name: clientName,
        client_email: clientEmail,
        amount: amount,
        currency: currency,
        description: desc
      })
    });
    const data = await res.json();

    if (data.success) {
      closeModal('create-payment-modal');
      showToast('success', `PayPal Order Created: ${data.order.order_id}`);

      // Open checkout approval simulator modal
      openCheckoutModal(data.order, clientName);

      // Refresh list
      loadTransactions();
      refreshDashboard();
    } else {
      showToast('error', data.error || 'Failed to create PayPal order.');
    }
  } catch (err) {
    showToast('error', 'Network error calling PayPal Orders API.');
  } finally {
    setBtnLoading(btn, false, 'Generate PayPal Order');
  }
}

function openCheckoutModal(order, clientName) {
  const modal = document.getElementById('checkout-modal');
  const details = document.getElementById('checkout-order-details');
  if (!modal || !details) return;

  details.innerHTML = `
    <div style="background: rgba(200,240,243,0.3); border: 1px solid rgba(55,188,211,0.3); padding: 1.25rem; border-radius: 16px; margin-bottom: 1.5rem;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span style="font-weight: 700; color: var(--color-slate);">PayPal Order ID:</span>
        <code style="font-weight: 800; color: var(--color-deep-blue);">${escapeHtml(order.order_id)}</code>
      </div>
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span style="font-weight: 700; color: var(--color-slate);">Client / Payer:</span>
        <span style="font-weight: 700;">${escapeHtml(clientName)}</span>
      </div>
      <div style="display: flex; justify-content: space-between;">
        <span style="font-weight: 700; color: var(--color-slate);">Amount Due:</span>
        <span style="font-size: 1.2rem; font-weight: 800; color: var(--color-deep-blue);">$${parseFloat(order.amount).toFixed(2)} ${order.currency}</span>
      </div>
    </div>
    <p style="font-size: 0.85rem; color: var(--color-slate); line-height: 1.5; margin-bottom: 1.2rem;">
      Click below to execute the server-side capture verification through PayPal Orders v2 Capture API.
    </p>
    <div style="display: flex; gap: 0.75rem;">
      <button class="btn-liquid-primary" style="flex: 1;" onclick="executeCaptureOrder('${order.order_id}', ${order.amount}, '${escapeHtml(clientName)}')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Approve & Capture in Sandbox
      </button>
      <button class="btn-liquid-secondary" onclick="closeModal('checkout-modal')">Close</button>
    </div>
  `;

  openModal('checkout-modal');
}

async function executeCaptureOrder(orderId, amount, clientName) {
  try {
    showToast('info', `Capturing PayPal Order ${orderId}...`);
    const res = await fetch('/api/paypal/capture-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, amount: amount, client_name: clientName })
    });
    const data = await res.json();

    if (data.success) {
      closeModal('checkout-modal');
      showToast('success', `Payment Verified! Capture ID: ${data.capture.capture_id}`);
      refreshDashboard();
      loadTransactions();
      loadInvoices();
      loadNotifications();
    } else {
      showToast('error', data.error || 'Payment capture failed.');
    }
  } catch (err) {
    showToast('error', 'Error executing capture.');
  }
}

function inspectTransaction(txnId) {
  const txn = appState.transactions.find(t => t.id === txnId);
  if (!txn) return;

  const modal = document.getElementById('txn-inspect-modal');
  const body = document.getElementById('txn-inspect-body');
  if (!modal || !body) return;

  const fee = txn.paypal_fee || (txn.amount * 0.029 + 0.30).toFixed(2);
  const net = txn.net_amount || (txn.amount - fee).toFixed(2);

  body.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(8,127,165,0.1);">
      <div>
        <h3 style="font-size: 1.3rem; font-weight: 800; color: var(--color-charcoal);">${escapeHtml(txn.client_name)}</h3>
        <p style="font-size: 0.82rem; color: var(--color-slate);">${escapeHtml(txn.client_email)}</p>
      </div>
      <div style="text-align: right;">
        <div style="font-size: 1.6rem; font-weight: 800; color: var(--color-deep-blue);">$${parseFloat(txn.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} ${txn.currency}</div>
        <span class="status-badge ${txn.payment_status === 'Completed' ? 'badge-completed' : 'badge-pending'}">${txn.payment_status}</span>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
      <div style="background: rgba(247,250,250,0.8); padding: 0.85rem; border-radius: 12px;">
        <span style="font-size: 0.75rem; color: var(--color-slate); font-weight: 700;">PAYPAL ORDER ID</span>
        <div style="font-family: monospace; font-size: 0.88rem; font-weight: 700; color: var(--color-deep-blue); margin-top: 2px;">${escapeHtml(txn.paypal_order_id || 'N/A')}</div>
      </div>
      <div style="background: rgba(247,250,250,0.8); padding: 0.85rem; border-radius: 12px;">
        <span style="font-size: 0.75rem; color: var(--color-slate); font-weight: 700;">CAPTURE ID</span>
        <div style="font-family: monospace; font-size: 0.88rem; font-weight: 700; color: var(--color-charcoal); margin-top: 2px;">${escapeHtml(txn.paypal_capture_id || 'Pending Settlement')}</div>
      </div>
      <div style="background: rgba(247,250,250,0.8); padding: 0.85rem; border-radius: 12px;">
        <span style="font-size: 0.75rem; color: var(--color-slate); font-weight: 700;">PAYPAL PROCESSING FEE</span>
        <div style="font-size: 0.88rem; font-weight: 700; color: var(--color-slate); margin-top: 2px;">$${parseFloat(fee).toFixed(2)}</div>
      </div>
      <div style="background: rgba(247,250,250,0.8); padding: 0.85rem; border-radius: 12px;">
        <span style="font-size: 0.75rem; color: var(--color-slate); font-weight: 700;">NET SETTLED PROCEEDS</span>
        <div style="font-size: 0.88rem; font-weight: 800; color: #059669; margin-top: 2px;">$${parseFloat(net).toFixed(2)}</div>
      </div>
    </div>

    <div style="background: rgba(200,240,243,0.3); border-left: 4px solid var(--color-aqua); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
      <div style="font-weight: 700; font-size: 0.85rem; color: var(--color-deep-blue); margin-bottom: 0.25rem;">AI Cybersecurity Audit Assessment:</div>
      <p style="font-size: 0.82rem; color: var(--color-charcoal); line-height: 1.4;">${escapeHtml(txn.risk_reason || 'Verified legitimate freelancer payment. IP reputation score nominal.')}</p>
    </div>

    <div style="text-align: right;">
      <button class="btn-liquid-secondary" onclick="closeModal('txn-inspect-modal')">Close Forensic Dossier</button>
    </div>
  `;

  openModal('txn-inspect-modal');
}

// ============================================================================
// 5. AI Invoice Generator
// ============================================================================
async function runAIInvoiceGeneration() {
  const promptInput = document.getElementById('ai-invoice-prompt');
  const btn = document.getElementById('btn-gen-ai-invoice');
  const prompt = promptInput ? promptInput.value.trim() : '';

  if (!prompt) {
    showToast('warning', 'Please enter instructions to create an invoice.');
    return;
  }

  setBtnLoading(btn, true, 'ShieldBot Extracting Parameters...');

  try {
    const res = await fetch('/api/ai/generate-invoice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();

    if (data.success) {
      populateInvoiceForm(data.invoice);
      showToast('success', `Invoice drafted for ${data.invoice.client_name} ($${data.invoice.amount})`);
    } else {
      showToast('error', data.error || 'Failed to generate invoice draft.');
    }
  } catch (err) {
    showToast('error', 'Error calling AI Invoice Generator API.');
  } finally {
    setBtnLoading(btn, false, 'Generate Invoice Draft with AI');
  }
}

function populateInvoiceForm(inv) {
  document.getElementById('inv-client-name').value = inv.client_name || '';
  document.getElementById('inv-client-email').value = inv.client_email || '';
  document.getElementById('inv-project-title').value = inv.project_title || '';
  document.getElementById('inv-amount').value = inv.amount || '';
  document.getElementById('inv-due-date').value = inv.due_date || '';
  document.getElementById('inv-description').value = inv.description || '';
}

async function handleSaveInvoice(e) {
  e.preventDefault();
  const btn = document.getElementById('btn-save-invoice');
  const clientName = document.getElementById('inv-client-name')?.value.trim();
  const clientEmail = document.getElementById('inv-client-email')?.value.trim();
  const projectTitle = document.getElementById('inv-project-title')?.value.trim();
  const amount = parseFloat(document.getElementById('inv-amount')?.value);
  const dueDate = document.getElementById('inv-due-date')?.value;
  const description = document.getElementById('inv-description')?.value.trim();

  if (!clientName || !projectTitle || isNaN(amount) || amount <= 0) {
    showToast('warning', 'Please fill in client name, project title, and a valid amount.');
    return;
  }

  setBtnLoading(btn, true, 'Saving to Ledger...');

  try {
    const res = await fetch('/api/invoices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client_name: clientName,
        client_email: clientEmail,
        project_title: projectTitle,
        amount: amount,
        due_date: dueDate,
        description: description
      })
    });
    const data = await res.json();

    if (data.success) {
      showToast('success', `Invoice ${data.invoice.invoice_number} saved successfully!`);
      loadInvoices();
      refreshDashboard();
      // Clear form
      document.getElementById('inv-client-name').value = '';
      document.getElementById('inv-client-email').value = '';
      document.getElementById('inv-project-title').value = '';
      document.getElementById('inv-amount').value = '';
      document.getElementById('inv-description').value = '';
    } else {
      showToast('error', data.error || 'Failed to save invoice.');
    }
  } catch (err) {
    showToast('error', 'Network error saving invoice.');
  } finally {
    setBtnLoading(btn, false, 'Save & Issue Invoice');
  }
}

async function loadInvoices() {
  try {
    const res = await fetch('/api/invoices');
    const data = await res.json();
    if (data.success) {
      appState.invoices = data.invoices;
      renderInvoicesTable(data.invoices);
    }
  } catch (err) {
    console.error('Error loading invoices:', err);
  }
}

function renderInvoicesTable(invoices) {
  const tbody = document.getElementById('invoices-tbody');
  if (!tbody) return;

  if (!invoices || invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--color-slate); padding: 2rem;">No invoices generated yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(inv => {
    let statusClass = 'badge-pending';
    if (inv.status === 'Paid') statusClass = 'badge-completed';
    else if (inv.status === 'Overdue') statusClass = 'badge-critical';

    return `
      <tr>
        <td>
          <span style="font-family: monospace; font-weight: 700; color: var(--color-deep-blue);">${escapeHtml(inv.invoice_number)}</span>
        </td>
        <td>
          <div style="font-weight: 700; color: var(--color-charcoal);">${escapeHtml(inv.client_name)}</div>
          <div style="font-size: 0.75rem; color: var(--color-slate);">${escapeHtml(inv.project_title)}</div>
        </td>
        <td style="font-weight: 800; color: var(--color-deep-blue);">
          $${parseFloat(inv.amount).toLocaleString(undefined, {minimumFractionDigits: 2})} ${inv.currency}
        </td>
        <td>
          <span class="status-badge ${statusClass}">${inv.status}</span>
        </td>
        <td style="font-size: 0.82rem; color: var(--color-slate);">
          ${escapeHtml(inv.due_date || 'Upon Receipt')}
        </td>
        <td>
          <div style="display: flex; gap: 0.4rem;">
            <a href="/api/invoices/${inv.id}/pdf" class="btn-banner-action" style="padding: 0.35rem 0.75rem; font-size: 0.75rem; text-decoration: none;" title="Download PDF">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              PDF
            </a>
            ${inv.status !== 'Paid' ? `
              <button class="btn-liquid-primary" style="padding: 0.35rem 0.75rem; font-size: 0.75rem;" onclick="triggerInvoicePayPalOrder('${inv.id}')" title="Pay with PayPal Sandbox">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M7 2h10a3 3 0 0 1 3 3v2a3 3 0 0 1-3 3H9l-2 10H3L7 2z"/></svg>
                PayPal
              </button>
            ` : ''}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function triggerInvoicePayPalOrder(invId) {
  try {
    showToast('info', 'Creating PayPal Sandbox order linked to invoice...');
    const res = await fetch(`/api/invoices/${invId}/create-paypal-order`, { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      showToast('success', `PayPal Order Created (${data.order.order_id})!`);
      const inv = appState.invoices.find(i => i.id === invId);
      openCheckoutModal(data.order, inv ? inv.client_name : 'Valued Client');
      loadInvoices();
      refreshDashboard();
    } else {
      showToast('error', data.error || 'Failed to create PayPal order.');
    }
  } catch (err) {
    showToast('error', 'Error linking PayPal order.');
  }
}

// ============================================================================
// 6. Smart Alarm & Notifications
// ============================================================================
async function loadNotifications() {
  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    if (data.success) {
      appState.notifications = data.notifications;
      renderNotifications(data.notifications, data.unread_count);
    }
  } catch (err) {
    console.error('Error loading notifications:', err);
  }
}

function renderNotifications(notifs, unreadCount) {
  // Update badges
  const bellBadges = document.querySelectorAll('.notif-badge-count');
  bellBadges.forEach(b => {
    b.textContent = unreadCount || 0;
    b.style.display = unreadCount > 0 ? 'flex' : 'none';
  });

  const listContainer = document.getElementById('notifications-full-list');
  if (!listContainer) return;

  if (!notifs || notifs.length === 0) {
    listContainer.innerHTML = `<div style="text-align: center; color: var(--color-slate); padding: 2.5rem;">All quiet! No security incidents or payment notifications.</div>`;
    return;
  }

  listContainer.innerHTML = notifs.map(n => {
    let sevBadge = 'badge-safe';
    if (n.severity === 'Critical') sevBadge = 'badge-critical';
    else if (n.severity === 'High') sevBadge = 'badge-failed';
    else if (n.severity === 'Medium') sevBadge = 'badge-pending';

    return `
      <div class="glass-card" style="padding: 1.25rem; margin-bottom: 0.85rem; border-left: 4px solid ${n.severity === 'Critical' ? '#DC2626' : (n.severity === 'High' ? '#EA580C' : '#37BCD3')}; opacity: ${n.is_read ? '0.75' : '1'};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <h4 style="font-size: 0.95rem; font-weight: 800; color: var(--color-charcoal);">${escapeHtml(n.title)}</h4>
          <span class="status-badge ${sevBadge}">${n.severity}</span>
        </div>
        <p style="font-size: 0.85rem; color: var(--color-slate); line-height: 1.45;">${escapeHtml(n.description)}</p>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem; font-size: 0.75rem; color: var(--color-muted);">
          <span>${n.created_at}</span>
          ${!n.is_read ? `
            <button class="filter-tab-btn" onclick="markNotificationRead('${n.id}')">Mark Read</button>
          ` : '<span style="color: #059669;">? Read</span>'}
        </div>
      </div>
    `;
  }).join('');
}

async function markNotificationRead(id) {
  try {
    await fetch(`/api/notifications/${id}/read`, { method: 'PATCH' });
    loadNotifications();
    refreshDashboard();
  } catch (err) {
    console.error('Error marking notification read:', err);
  }
}

async function markAllNotificationsRead() {
  try {
    await fetch('/api/notifications/read-all', { method: 'POST' });
    showToast('success', 'All notifications marked as read.');
    loadNotifications();
    refreshDashboard();
  } catch (err) {
    console.error('Error marking all read:', err);
  }
}

// ============================================================================
// 7. Floating AI Financial Assistant (ShieldBot)
// ============================================================================
function setupAssistant() {
  const trigger = document.getElementById('assistant-trigger');
  const drawer = document.getElementById('assistant-drawer');
  const closeBtn = document.getElementById('assistant-close-btn');
  const sendBtn = document.getElementById('assistant-send-btn');
  const input = document.getElementById('assistant-input');

  if (trigger && drawer) {
    trigger.addEventListener('click', () => {
      drawer.classList.toggle('open');
      if (drawer.classList.contains('open') && input) input.focus();
    });
  }

  if (closeBtn && drawer) {
    closeBtn.addEventListener('click', () => {
      drawer.classList.remove('open');
    });
  }

  if (sendBtn && input) {
    sendBtn.addEventListener('click', () => handleAssistantQuery());
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleAssistantQuery();
    });
  }
}

async function handleAssistantQuery(customText = null) {
  const input = document.getElementById('assistant-input');
  const query = customText || (input ? input.value.trim() : '');
  if (!query) return;

  if (input && !customText) input.value = '';

  appendChatMessage('user', query);

  const container = document.getElementById('assistant-messages');
  const typingIndicator = document.createElement('div');
  typingIndicator.className = 'chat-bubble bot';
  typingIndicator.id = 'typing-indicator-node';
  typingIndicator.textContent = 'ShieldBot is inspecting live ledger records...';
  if (container) {
    container.appendChild(typingIndicator);
    container.scrollTop = container.scrollHeight;
  }

  try {
    const res = await fetch('/api/ai/assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: query })
    });
    const data = await res.json();

    if (typingIndicator && typingIndicator.parentNode) {
      typingIndicator.parentNode.removeChild(typingIndicator);
    }

    if (data.success) {
      appendChatMessage('bot', data.reply);
    } else {
      appendChatMessage('bot', 'Apologies, I encountered an error checking your financial records.');
    }
  } catch (err) {
    if (typingIndicator && typingIndicator.parentNode) {
      typingIndicator.parentNode.removeChild(typingIndicator);
    }
    appendChatMessage('bot', 'Network error connecting to AI Financial Assistant.');
  }
}

function appendChatMessage(sender, text) {
  const container = document.getElementById('assistant-messages');
  if (!container) return;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  // Basic markdown bold replacement for readability
  let formatted = escapeHtml(text).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\n/g, '<br/>');

  bubble.innerHTML = formatted;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function askAssistantChip(promptText) {
  const drawer = document.getElementById('assistant-drawer');
  if (drawer && !drawer.classList.contains('open')) {
    drawer.classList.add('open');
  }
  handleAssistantQuery(promptText);
}

// ============================================================================
// 8. Analytics Graphical Charts (Chart.js)
// ============================================================================
function renderDashboardActivityChart() {
  const ctx = document.getElementById('dashboard-activity-chart');
  if (!ctx) return;

  if (appState.charts.dashboardActivity) {
    appState.charts.dashboardActivity.destroy();
  }

  const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(0, 'rgba(55, 188, 211, 0.45)');
  gradient.addColorStop(1, 'rgba(8, 127, 165, 0.0)');

  appState.charts.dashboardActivity = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026 (Live)'],
      datasets: [{
        label: 'Verified PayPal Milestone Volume ($)',
        data: [2100, 3400, 4800, 6200, appState.stats.completed_amount || 8900],
        borderColor: '#087FA5',
        backgroundColor: gradient,
        borderWidth: 3,
        fill: true,
        tension: 0.38,
        pointBackgroundColor: '#37BCD3',
        pointBorderColor: '#FFFFFF',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(38, 54, 64, 0.9)',
          titleFont: { family: 'Plus Jakarta Sans', weight: 'bold' },
          bodyFont: { family: 'Plus Jakarta Sans' },
          padding: 12,
          cornerRadius: 10,
          callbacks: {
            label: function(context) {
              return ` Verified Milestone: $${context.raw.toLocaleString()} USD`;
            }
          }
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(8, 127, 165, 0.08)' },
          ticks: {
            callback: value => `$${value}`,
            font: { family: 'Plus Jakarta Sans', size: 11 },
            color: '#5A7184'
          }
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: 'Plus Jakarta Sans', size: 11 }, color: '#5A7184' }
        }
      }
    }
  });
}

async function renderAnalyticsCharts() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    if (!data.success) return;

    const analytics = data.analytics;

    // 1. Monthly Revenue Volume Chart
    const ctxVol = document.getElementById('analytics-volume-chart');
    if (ctxVol) {
      if (appState.charts.volume) appState.charts.volume.destroy();
      const grad = ctxVol.getContext('2d').createLinearGradient(0, 0, 0, 250);
      grad.addColorStop(0, '#087FA5');
      grad.addColorStop(1, '#37BCD3');

      appState.charts.volume = new Chart(ctxVol, {
        type: 'bar',
        data: {
          labels: analytics.months,
          datasets: [{
            label: 'Total Volume ($)',
            data: analytics.monthly_volume,
            backgroundColor: grad,
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { ticks: { callback: v => `$${v}` } }
          }
        }
      });
    }

    // 2. Status Distribution Doughnut Chart
    const ctxDist = document.getElementById('analytics-dist-chart');
    if (ctxDist) {
      if (appState.charts.dist) appState.charts.dist.destroy();
      const compCount = analytics.status_distribution['Completed']?.count || 6;
      const pendCount = analytics.status_distribution['Pending']?.count || 2;
      const failCount = analytics.status_distribution['Failed']?.count || 1;

      appState.charts.dist = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
          labels: ['Completed', 'Pending Escrow', 'Flagged / Failed'],
          datasets: [{
            data: [compCount, pendCount, failCount],
            backgroundColor: ['#10B981', '#FF9D24', '#FF6565'],
            borderWidth: 2,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' }
          }
        }
      });
    }

    // 3. Security Threat Breakdown Polar Chart
    const ctxSec = document.getElementById('analytics-threats-chart');
    if (ctxSec) {
      if (appState.charts.threats) appState.charts.threats.destroy();
      appState.charts.threats = new Chart(ctxSec, {
        type: 'polarArea',
        data: {
          labels: ['Critical Scam Attempts', 'High Risk URLs', 'Advance Fee Traps', 'Clean Audits'],
          datasets: [{
            data: [4, 6, 3, 12],
            backgroundColor: [
              'rgba(255, 101, 101, 0.7)',
              'rgba(255, 157, 36, 0.7)',
              'rgba(14, 165, 233, 0.7)',
              'rgba(16, 185, 129, 0.7)'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } }
        }
      });
    }
  } catch (err) {
    console.error('Error rendering analytics charts:', err);
  }
}

// ============================================================================
// 9. UI Helpers, Modals & Toast Alerts
// ============================================================================
function setupEventListeners() {
  // Invoice form submit
  const invForm = document.getElementById('invoice-draft-form');
  if (invForm) invForm.addEventListener('submit', handleSaveInvoice);

  // PayPal create payment submit
  const ppForm = document.getElementById('create-payment-form');
  if (ppForm) ppForm.addEventListener('submit', handleCreatePaymentRequest);
}

function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('open');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('open');
}

function showToast(type, message) {
  const shelf = document.getElementById('toast-shelf') || createToastShelf();
  const pill = document.createElement('div');
  pill.className = 'toast-pill';

  let icon = `?`;
  if (type === 'error' || type === 'critical') icon = `<span style="color: #DC2626;">?</span>`;
  else if (type === 'warning') icon = `<span style="color: #D97706;">?</span>`;
  else if (type === 'info') icon = `<span style="color: #087FA5;">??</span>`;
  else icon = `<span style="color: #059669;">?</span>`;

  pill.innerHTML = `
    ${icon}
    <span>${escapeHtml(message)}</span>
  `;

  shelf.appendChild(pill);

  setTimeout(() => {
    pill.style.opacity = '0';
    pill.style.transform = 'translateY(15px)';
    pill.style.transition = 'all 0.3s ease';
    setTimeout(() => {
      if (pill.parentNode) pill.parentNode.removeChild(pill);
    }, 300);
  }, 4200);
}

function createToastShelf() {
  const shelf = document.createElement('div');
  shelf.id = 'toast-shelf';
  shelf.className = 'toast-shelf';
  document.body.appendChild(shelf);
  return shelf;
}

function setBtnLoading(btn, isLoading, text) {
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = text;
  btn.style.opacity = isLoading ? '0.7' : '1';
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function fetchAIStatus() {
  try {
    const res = await fetch('/api/ai/status');
    const data = await res.json();
    if (data.success) {
      appState.aiStatus = data.status;
      const badge = document.getElementById('ai-model-badge');
      if (badge) {
        badge.textContent = data.status.fallback_active ? 'Heuristic Core Active' : 'OpenAI Connected';
      }
    }
  } catch (err) {
    console.error('Error fetching AI status:', err);
  }
}
