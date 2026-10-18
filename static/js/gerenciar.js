
document.addEventListener('submit', (event) => {
  const form = event.target.closest('form[data-confirm]');
  if (form && !confirm(form.dataset.confirm)) event.preventDefault();
});