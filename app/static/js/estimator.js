/**
 * Estimator screen JS
 * - Live bid calculations (crew internal cost, crew bid, equipment totals)
 * - Equipment row add/remove
 * - Auto-fill equipment rate from dropdown
 * - Default equipment hours to crew hours
 */

document.addEventListener('DOMContentLoaded', function () {
  initCalculations();
  initEquipmentTable();
  restoreEquipTotals();
});

// ── Live Calculations ────────────────────────────────────────

function initCalculations() {
  const pkgSelect   = document.getElementById('crew_package_key');
  const hoursInput  = document.getElementById('crew_hours');
  const marginInput = document.getElementById('margin_pct');

  if (!pkgSelect || !hoursInput || !marginInput) return;

  [pkgSelect, hoursInput, marginInput].forEach(function (el) {
    el.addEventListener('change', recalculate);
    el.addEventListener('input', recalculate);
  });

  // Restore saved estimate values on load
  if (typeof ESTIMATE_DATA !== 'undefined' && ESTIMATE_DATA.total) {
    document.getElementById('total-subtotal').textContent = fmtCurrency(ESTIMATE_DATA.subtotal);
    document.getElementById('total-tax').textContent      = fmtCurrency(ESTIMATE_DATA.tax_amount);
    document.getElementById('total-grand').textContent    = fmtCurrency(ESTIMATE_DATA.total);
    if (ESTIMATE_DATA.tax_rate) {
      document.getElementById('tax-rate-label').textContent =
        '(' + (ESTIMATE_DATA.tax_rate * 100).toFixed(1) + '%)';
    }
    document.getElementById('equip-total-display').textContent =
      fmtCurrency(ESTIMATE_DATA.equipment_total || 0);
  }

  recalculate();
}

function recalculate() {
  const pkgKey = document.getElementById('crew_package_key').value;
  const hours  = parseFloat(document.getElementById('crew_hours').value) || 0;
  const margin = parseFloat(document.getElementById('margin_pct').value) || 0;

  let rate = 0;
  if (pkgKey && typeof CREW_RATES !== 'undefined' && CREW_RATES[pkgKey]) {
    rate = CREW_RATES[pkgKey].rate;
  }

  // Update rate display
  const rateDisplay = document.getElementById('crew-rate-display');
  if (rateDisplay) {
    rateDisplay.textContent = rate > 0 ? fmtCurrency(rate) + '/hr' : '—';
  }

  // Crew calculations
  const internalCost = hours * rate;
  let crewBid = 0;
  if (margin > 0 && margin < 100) {
    crewBid = internalCost / (1 - margin / 100);
  } else if (margin >= 100) {
    crewBid = internalCost;
  }

  document.getElementById('calc-internal').textContent = fmtCurrency(internalCost);
  document.getElementById('calc-crew-bid').textContent = fmtCurrency(crewBid);

  // Equipment total from table
  const equipTotal = calcEquipTotal();
  document.getElementById('equip-total-display').textContent = fmtCurrency(equipTotal);

  // Subtotal (crew bid + equip total)
  const subtotal = crewBid + equipTotal;
  document.getElementById('total-subtotal').textContent = fmtCurrency(subtotal);

  // Tax — shown from saved estimate data only; live lookup happens on server
  // We keep the last-saved tax values displayed if available
  // (server does the actual WA DOR lookup on save)
}

// ── Equipment Table ───────────────────────────────────────────

function initEquipmentTable() {
  const addBtn = document.getElementById('add-equipment-btn');
  const tbody  = document.getElementById('equipment-tbody');
  const template = document.getElementById('equip-row-template');

  if (!addBtn || !tbody || !template) return;

  addBtn.addEventListener('click', function () {
    const clone = template.content.cloneNode(true);
    const row = clone.querySelector('tr');

    // Default hours to current crew hours
    const crewHours = parseFloat(document.getElementById('crew_hours').value) || '';
    const hoursInput = row.querySelector('.equip-hours');
    if (hoursInput && crewHours) hoursInput.value = crewHours;

    // Wire up equipment select change
    const keySelect = row.querySelector('.equip-key');
    keySelect.addEventListener('change', function () { onEquipKeyChange(row); });

    // Wire up hours change
    hoursInput.addEventListener('input', function () { onEquipChange(row); });

    // Wire up remove button
    const removeBtn = row.querySelector('.equip-remove');
    removeBtn.addEventListener('click', function () {
      row.remove();
      calcEquipTotal();
      recalculate();
    });

    tbody.appendChild(row);
  });

  // Wire up existing rows
  tbody.querySelectorAll('.equip-row').forEach(function (row) {
    const keySelect = row.querySelector('.equip-key');
    const hoursInput = row.querySelector('.equip-hours');
    const removeBtn = row.querySelector('.equip-remove');

    if (keySelect) keySelect.addEventListener('change', function () { onEquipKeyChange(row); });
    if (hoursInput) hoursInput.addEventListener('input', function () { onEquipChange(row); });
    if (removeBtn) removeBtn.addEventListener('click', function () {
      row.remove();
      calcEquipTotal();
      recalculate();
    });
  });
}

function onEquipKeyChange(row) {
  const keySelect = row.querySelector('.equip-key');
  const rateInput = row.querySelector('.equip-rate');
  const selected = keySelect.options[keySelect.selectedIndex];
  const rate = parseFloat(selected.getAttribute('data-rate')) || 0;
  if (rateInput) rateInput.value = rate.toFixed(2);
  onEquipChange(row);
}

function onEquipChange(row) {
  const hoursInput = row.querySelector('.equip-hours');
  const rateInput  = row.querySelector('.equip-rate');
  const totalSpan  = row.querySelector('.equip-total');
  const totalHidden = row.querySelector('.equip-total-hidden');

  const hours = parseFloat(hoursInput ? hoursInput.value : 0) || 0;
  const rate  = parseFloat(rateInput ? rateInput.value : 0) || 0;
  const total = hours * rate;

  if (totalSpan) totalSpan.textContent = fmtCurrency(total);
  if (totalHidden) totalHidden.value = total.toFixed(2);

  calcEquipTotal();
  recalculate();
}

function calcEquipTotal() {
  const rows = document.querySelectorAll('#equipment-tbody .equip-row');
  let total = 0;
  rows.forEach(function (row) {
    const hoursInput = row.querySelector('.equip-hours');
    const rateInput  = row.querySelector('.equip-rate');
    const hours = parseFloat(hoursInput ? hoursInput.value : 0) || 0;
    const rate  = parseFloat(rateInput ? rateInput.value : 0) || 0;
    total += hours * rate;
  });
  const display = document.getElementById('equip-total-display');
  if (display) display.textContent = fmtCurrency(total);
  return total;
}

function restoreEquipTotals() {
  // Recompute display totals for existing rows on page load
  document.querySelectorAll('#equipment-tbody .equip-row').forEach(function (row) {
    const hoursInput = row.querySelector('.equip-hours');
    const rateInput  = row.querySelector('.equip-rate');
    const totalSpan  = row.querySelector('.equip-total');

    const hours = parseFloat(hoursInput ? hoursInput.value : 0) || 0;
    const rate  = parseFloat(rateInput ? rateInput.value : 0) || 0;
    if (totalSpan) totalSpan.textContent = fmtCurrency(hours * rate);
  });
}

// ── PDF Generation Confirm ────────────────────────────────────

function confirmGenerate() {
  const pkg    = document.getElementById('crew_package_key').value;
  const hours  = document.getElementById('crew_hours').value;
  const margin = document.getElementById('margin_pct').value;

  if (!pkg || !hours || !margin) {
    alert('Please fill in Crew Package, Hours, and Margin % before generating a PDF.');
    return false;
  }
  return true;
}

// ── Helpers ──────────────────────────────────────────────────

function fmtCurrency(value) {
  if (isNaN(value) || value === null) return '$0.00';
  return '$' + parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
