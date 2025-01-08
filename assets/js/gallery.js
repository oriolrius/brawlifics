document.addEventListener('DOMContentLoaded', () => {
  const gallery = document.getElementById('gallery');
  const fileUpload = document.getElementById('file-upload');

  async function loadGalleryImages() {
      try {
          const response = await fetch('/api/gallery');
          const images = await response.json();
          gallery.innerHTML = ''; // Clear existing items
          images.forEach(img => {
              gallery.appendChild(createGalleryItem(img.name, img.path));
          });
      } catch (error) {
          console.error('Error loading gallery images:', error);
      }
  }

  function createGalleryItem(name, path) {
      const div = document.createElement('div');
      div.className = 'gallery-item';
      if (localStorage.getItem('player_image') === path) {
          div.classList.add('selected');
      }

      div.innerHTML = `
          <img src="${path}" alt="${name}">
          <h3>${name}</h3>
      `;

      div.addEventListener('click', () => {
          document.querySelectorAll('.gallery-item').forEach(item => {
              item.classList.remove('selected');
          });
          div.classList.add('selected');
          localStorage.setItem('player_image', path);
      });

      return div;
  }

  fileUpload.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) {
          const formData = new FormData();
          formData.append('file', file);

          try {
              const response = await fetch('/api/gallery', {
                  method: 'POST',
                  body: formData
              });

              if (response.ok) {
                  const result = await response.json();
                  gallery.appendChild(createGalleryItem(result.name, result.path));
              }
          } catch (error) {
              console.error('Error uploading image:', error);
          }
      }
  });

  // Initial load of images
  loadGalleryImages();
});