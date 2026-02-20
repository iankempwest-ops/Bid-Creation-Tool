/**
 * Admin intake form JS
 * - Customer autocomplete / fill
 * - Phone formatting
 * - Specs character counter
 * - Client-side validation hints
 */

document.addEventListener('DOMContentLoaded', function () {
  initCustomerAutocomplete();
  initPhoneFormat();
  initSpecsCounter();
});

// ── Customer Autocomplete ────────────────────────────────────

function initCustomerAutocomplete() {
  const input = document.getElementById('customer_name');
  if (!input) return;

  const dropdown = document.getElementById('customer-suggestions');
  const customerIdInput = document.getElementById('customer_id');
  const existingNotice = document.getElementById('existing-customer-notice');
  const existingMsg = document.getElementById('existing-customer-msg');

  if (!dropdown) return;

  let debounceTimer = null;
  let selectedCustomerId = null;

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const q = input.value.trim();

    if (q.length < 1) {
      hideDropdown();
      clearExistingNotice();
      return;
    }

    debounceTimer = setTimeout(function () {
      fetch('/api/customers/search?q=' + encodeURIComponent(q))
        .then(function (r) { return r.json(); })
        .then(function (customers) {
          renderSuggestions(customers);
        })
        .catch(function () { hideDropdown(); });
    }, 200);
  });

  function renderSuggestions(customers) {
    dropdown.innerHTML = '';
    if (!customers || customers.length === 0) {
      hideDropdown();
      return;
    }

    customers.forEach(function (c) {
      const item = document.createElement('div');
      item.className = 'suggestion-item';
      const sub = [c.billing_city, c.billing_state].filter(Boolean).join(', ');
      item.innerHTML =
        '<div class="sug-name">' + escHtml(c.name) + '</div>' +
        (sub ? '<div class="sug-sub">' + escHtml(sub) + (c.phone ? ' &bull; ' + escHtml(c.phone) : '') + '</div>' : '');

      item.addEventListener('mousedown', function (e) {
        e.preventDefault(); // prevent blur before click
        fillCustomer(c);
        hideDropdown();
      });

      dropdown.appendChild(item);
    });

    dropdown.classList.remove('hidden');
  }

  function fillCustomer(c) {
    input.value = c.name;
    selectedCustomerId = c.id;

    if (customerIdInput) customerIdInput.value = c.id;

    // Fill fields
    setVal('contact_name', c.primary_contact_name || '');
    setVal('phone', c.phone || '');
    setVal('email', c.email || '');
    setVal('billing_street', c.billing_street || '');
    setVal('billing_city', c.billing_city || '');
    setVal('billing_state', c.billing_state || '');
    setVal('billing_zip', c.billing_zip || '');

    // Show "update defaults?" notice
    if (existingNotice && existingMsg) {
      existingMsg.textContent = 'Existing customer found: ' + c.name;
      existingNotice.classList.remove('hidden');
    }
  }

  function clearExistingNotice() {
    if (existingNotice) existingNotice.classList.add('hidden');
    if (customerIdInput) customerIdInput.value = '';
    selectedCustomerId = null;
  }

  function hideDropdown() {
    dropdown.classList.add('hidden');
    dropdown.innerHTML = '';
  }

  // Hide on outside click
  document.addEventListener('click', function (e) {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      hideDropdown();
    }
  });

  // Clear customer link on manual edit of name
  input.addEventListener('keydown', function (e) {
    if (e.key !== 'Tab' && e.key !== 'Enter') {
      if (selectedCustomerId) {
        clearExistingNotice();
      }
    }
  });
}

// ── Phone Auto-Format ────────────────────────────────────────

function initPhoneFormat() {
  const phoneInput = document.getElementById('phone');
  if (!phoneInput) return;

  phoneInput.addEventListener('blur', function () {
    const digits = phoneInput.value.replace(/\D/g, '');
    const err = document.getElementById('phone-error');
    if (!digits) {
      if (err) err.textContent = '';
      return;
    }
    if (digits.length !== 10) {
      if (err) err.textContent = 'Phone must be 10 digits.';
      phoneInput.classList.add('error');
      return;
    }
    phoneInput.classList.remove('error');
    phoneInput.value = '(' + digits.slice(0, 3) + ') ' + digits.slice(3, 6) + '-' + digits.slice(6);
    if (err) err.textContent = '';
  });

  phoneInput.addEventListener('input', function () {
    const err = document.getElementById('phone-error');
    if (err) err.textContent = '';
    phoneInput.classList.remove('error');
  });
}

// ── Specs Character Counter ───────────────────────────────────

function initSpecsCounter() {
  const ta = document.getElementById('specs');
  const counter = document.getElementById('specs-count');
  if (!ta || !counter) return;

  ta.addEventListener('input', function () {
    counter.textContent = ta.value.length;
    if (ta.value.length < 10) {
      counter.style.color = '#c62828';
    } else {
      counter.style.color = '';
    }
  });
}

// ── Helpers ──────────────────────────────────────────────────

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val;
}

function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}
