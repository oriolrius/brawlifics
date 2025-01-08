document.addEventListener('DOMContentLoaded', async () => {
  // Fetch and display version
  fetch('/api/version')
    .then(response => response.json())
    .then(data => {
      document.getElementById('version-footer').textContent = `v${data.version}`;
      console.debug('Version:', data.version);
    })
    .catch(error => {
      console.error('Error fetching version:', error);
      document.getElementById('version-footer').textContent = 'Version unknown';
    });
});
