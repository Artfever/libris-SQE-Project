(() => {
  const theme = localStorage.getItem('theme');
  if (theme === 'verdigris') {
    document.documentElement.setAttribute('data-theme', theme);
  }
  document.documentElement.classList.add('theme-ready');
})();
