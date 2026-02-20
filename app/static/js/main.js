// Shared utilities

/**
 * Format a number as currency string: $1,234.56
 */
function fmtCurrency(value) {
  if (isNaN(value) || value === null) return '$0.00';
  return '$' + parseFloat(value).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Auto-dismiss flash messages after 5 seconds
 */
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 500);
    }, 5000);
  });
});
