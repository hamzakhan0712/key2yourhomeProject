
// Initialize property galleries
function initPropertyGallery(vid_img,propertyId, mediaItems, elements) {
    // State management
    let currentIndex = 0;
    
    // Initialize the gallery
    function initGallery() {
        if (mediaItems.length === 0) {
            showEmptyState();
            return;
        }
        
        renderMainPreview(mediaItems[0], vid_img);
        renderThumbnails(vid_img);
        setupEventListeners();
        setupThumbnailNavigation();
    }

    // Show empty state
    function showEmptyState() {
        elements.mainPreview.innerHTML = `
            <div class="w-full h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
                <div class="text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p class="mt-2">No media available for this property</p>
                </div>
            </div>
        `;
    }

    // Render the main preview
    function renderMainPreview(item, vid_img) {
        if (!item) return;
        
        elements.mainPreview.innerHTML = '';
        const mediaContainer = document.createElement('div');
        mediaContainer.className = 'relative w-full h-full flex items-center justify-center';
        
        const mediaElement = createMediaElement(item,vid_img, true);
        mediaElement.addEventListener('click', openFullscreen);
        mediaContainer.appendChild(mediaElement);
        elements.mainPreview.appendChild(mediaContainer);
        
        // Add caption if available
        if (item.title || item.about) {
            const caption = document.createElement('div');
            caption.className = 'absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4 text-white';
            if (item.title) {
                const title = document.createElement('h3');
                title.className = 'font-bold';
                title.textContent = item.title;
                caption.appendChild(title);
            }
            if (item.about) {
                const about = document.createElement('p');
                about.className = 'text-sm mt-1';
                about.textContent = item.about;
                caption.appendChild(about);
            }
            elements.mainPreview.appendChild(caption);
        }
    }

    // Create media element (image or video)
    function createMediaElement(item, vid_img, isMainPreview = false) {
        if (item.type === 'image') {
            const container = document.createElement('div');
            container.className = 'relative w-full h-full flex items-center justify-center';
            
            const img = document.createElement('img');
            img.src = item.url;
            img.alt = item.alt || '';
            img.className = 'max-h-full max-w-full object-contain cursor-zoom-in';
            img.style.objectFit = 'contain';
            img.loading = isMainPreview ? 'eager' : 'lazy';
            img.decoding = 'async';
            
            // Set fixed container height and handle image sizing
            container.style.height = '300px'; // Fixed height for all images
            container.style.width = '100%';
            container.style.overflow = 'hidden';
            container.style.display = 'flex';
            container.style.alignItems = 'center';
            container.style.justifyContent = 'center';
            
            img.onload = function() {
                // Calculate the appropriate dimensions to maintain aspect ratio
                const containerHeight = 300; // Fixed height
                const containerWidth = container.clientWidth;
                
                const imgRatio = img.naturalWidth / img.naturalHeight;
                const containerRatio = containerWidth / containerHeight;
                
                if (imgRatio > containerRatio) {
                    // Image is wider than container - fit to width
                    img.style.width = '100%';
                    img.style.height = 'auto';
                    img.style.maxHeight = 'none';
                } else {
                    // Image is taller than container - fit to height
                    img.style.height = '100%';
                    img.style.width = 'auto';
                    img.style.maxWidth = 'none';
                }
                
                // Center the image
                img.style.display = 'block';
                img.style.margin = '0 auto';
            };
            
            // Handle window resize to maintain proper sizing
            const resizeObserver = new ResizeObserver(() => {
                if (img.complete) {
                    img.onload(); // Trigger resize handler
                }
            });
            resizeObserver.observe(container);
            
            container.appendChild(img);
            return container;
        } 
        
        if (item.type === 'video') {
            const container = document.createElement('div');
            container.className = 'relative w-full h-full flex items-center justify-center';
            
            // Set fixed height and other styles just like image
            container.style.height = '300px';
            container.style.width = '100%';
            container.style.overflow = 'hidden';
            container.style.display = 'flex';
            container.style.alignItems = 'center';
            container.style.justifyContent = 'center';
        
            const video = document.createElement('video');
            video.src = item.url;
            video.controls = true;
            video.playsInline = true;
            video.className = 'object-contain cursor-zoom-in';
            video.style.objectFit = 'contain';
            video.style.display = 'block';
            video.style.margin = '0 auto';
            video.style.maxHeight = '100%';
            video.style.maxWidth = '100%';
            video.style.height = 'auto';
            video.style.width = 'auto';
        
            if (vid_img) {
                video.poster = vid_img;
            }
        
            // Maintain aspect ratio during window resize
            video.onloadedmetadata = function () {
                const containerHeight = 300;
                const containerWidth = container.clientWidth;
        
                const videoRatio = video.videoWidth / video.videoHeight;
                const containerRatio = containerWidth / containerHeight;
        
                if (videoRatio > containerRatio) {
                    video.style.width = '100%';
                    video.style.height = 'auto';
                    video.style.maxHeight = 'none';
                } else {
                    video.style.height = '100%';
                    video.style.width = 'auto';
                    video.style.maxWidth = 'none';
                }
            };
        
            const resizeObserver = new ResizeObserver(() => {
                if (video.readyState >= 1) {
                    video.onloadedmetadata();
                }
            });
            resizeObserver.observe(container);
        
            // Prevent fullscreen open from UI controls clicks
            video.addEventListener('click', (e) => {
                if (!e.target.classList.contains('controls')) {
                    openFullscreen();
                }
            });
        
            container.appendChild(video);
            return container;
        }
        
        
        // Handle unsupported media types
        const fallback = document.createElement('div');
        fallback.className = 'w-full h-[300px] flex items-center justify-center bg-gray-200 dark:bg-gray-700';
        fallback.innerHTML = `
            <div class="text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <p class="mt-2 text-gray-500 dark:text-gray-400">Unsupported media type</p>
            </div>
        `;
        return fallback;
    }

    function renderThumbnails(vid_img) {
        elements.mediaThumbnails.innerHTML = '';
        elements.fullscreenThumbnails.innerHTML = '';

        mediaItems.forEach((item, index) => {
            // Create thumbnail wrapper button
            const thumb = document.createElement('button');
            thumb.className = `flex-shrink-0 relative cursor-pointer transition-all duration-200 ease-in-out ${
                index === currentIndex ? 'ring-2 ring-blue-500 scale-105' : 'hover:ring-1 hover:ring-blue-300'
            }`;
            thumb.setAttribute('aria-label', `View media item ${index + 1}`);
            thumb.setAttribute('data-index', index);

            // Create thumbnail content container
            const thumbContent = document.createElement('div');
            thumbContent.className = 'relative h-20 w-20 rounded-md overflow-hidden bg-gray-200 dark:bg-gray-700';

            if (item.type === 'image') {
                const img = document.createElement('img');
                img.src = item.thumb || item.url;
                img.alt = item.alt || '';
                img.className = 'w-12 h-12 object-cover';
                img.loading = 'lazy';
                thumbContent.appendChild(img);
            } else if (item.type === 'video') {
                // Create container for video preview
                const videoContainer = document.createElement('div');
                videoContainer.className = 'relative w-full h-full group';
                
                // Add thumbnail image
                const thumbImage = document.createElement('img');
                thumbImage.src = vid_img;

                thumbImage.alt = 'Video thumbnail';
                thumbImage.className = 'w-12 h-12 object-cover';
                thumbImage.loading = 'lazy';
                videoContainer.appendChild(thumbImage);

                // Add video element that will play on hover
                const previewVideo = document.createElement('video');
                previewVideo.src = item.url;
                previewVideo.muted = true;
                previewVideo.loop = true;
                previewVideo.className = 'absolute inset-0 w-full h-12 object-cover opacity-0 group-hover:opacity-100 transition-opacity duration-300';
                
                // Start playing on hover
                thumb.addEventListener('mouseenter', () => {
                    previewVideo.play().catch(e => console.log('Video play failed:', e));
                });
                
                // Pause when not hovering
                thumb.addEventListener('mouseleave', () => {
                    previewVideo.pause();
                    previewVideo.currentTime = 0;
                });
                
                videoContainer.appendChild(previewVideo);

                // Overlay play icon (shown when not hovering)
                const overlay = document.createElement('div');
                overlay.className = 'absolute inset-0 flex items-center justify-center z-10 group-hover:opacity-0 transition-opacity duration-300';
                overlay.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                    </svg>
                `;
                videoContainer.appendChild(overlay);

                thumbContent.appendChild(videoContainer);
            } else {
                // Unsupported type fallback
                thumbContent.classList.add('flex', 'items-center', 'justify-center');
                thumbContent.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                `;
            }

            thumb.appendChild(thumbContent);

            // Clone into both containers
            elements.mediaThumbnails.appendChild(thumb.cloneNode(true));
            elements.fullscreenThumbnails.appendChild(thumb);
        });
    }

    // Update all gallery views
    function updateGallery() {
        if (mediaItems.length === 0) return;
        
        const item = mediaItems[currentIndex];
        renderMainPreview(item);
        
        // Update active thumbnail in both containers
        document.querySelectorAll(`#media-thumbnails-${propertyId} button, #fullscreen-thumbnails-${propertyId} button`).forEach((btn, idx) => {
            if (idx === currentIndex) {
                btn.classList.add('ring-2', 'ring-blue-500', 'scale-105');
                btn.classList.remove('hover:ring-1', 'hover:ring-blue-300');
            } else {
                btn.classList.remove('ring-2', 'ring-blue-500', 'scale-105');
                btn.classList.add('hover:ring-1', 'hover:ring-blue-300');
            }
        });
        
        // If in fullscreen mode, update the fullscreen view
        if (!elements.fullscreenModal.classList.contains('hidden')) {
            renderFullscreenPreview(item);
        }
        
        // Update thumbnail navigation arrows visibility
        updateThumbnailArrows();
    }

    // Open fullscreen view
    function openFullscreen() {
        if (mediaItems.length === 0) return;
        
        const item = mediaItems[currentIndex];
        renderFullscreenPreview(item);
        
        elements.fullscreenModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';
    }



    function renderFullscreenPreview(item) {
        elements.fullscreenPreview.innerHTML = '';
        
        // Update title and about
        document.getElementById(`fullscreen-title-${propertyId}`).textContent = item.title || '';
        document.getElementById(`fullscreen-about-${propertyId}`).textContent = item.about || '';
        
        // Update media counter
        document.getElementById(`current-index-${propertyId}`).textContent = currentIndex + 1;
        document.getElementById(`total-media-${propertyId}`).textContent = mediaItems.length;
        
        const mediaContainer = document.createElement('div');
        mediaContainer.className = 'relative w-full h-full flex items-center justify-center';
        
        if (item.type === 'image') {
            const img = document.createElement('img');
            img.src = item.url;
            img.alt = item.alt || '';
            img.className = ' object-contain cursor-zoom-out mt-20';
            img.height = '100px'
            img.loading = 'eager';
            img.onclick = closeFullscreenHandler;
            

                 // Apply smaller size via JS as fallback (optional)
            img.style.maxWidth = '80vw';
            img.style.maxHeight = '80vh';

            // Optional: Add border or padding for nicer display
            img.style.borderRadius = '8px';
            img.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';


            // Add zoom/pan functionality
            let scale = 1;
            let isDragging = false;
            let startX, startY, translateX = 0, translateY = 0;
            
            img.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = -e.deltaY;
                const zoomIntensity = 0.1;
                
                scale *= Math.exp(delta * zoomIntensity / 100);
                scale = Math.max(0.5, Math.min(scale, 5)); // Limit zoom
                
                img.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
                img.style.cursor = scale > 1 ? 'grab' : 'zoom-out';
            });
            
            img.addEventListener('mousedown', (e) => {
                if (scale > 1) {
                    isDragging = true;
                    startX = e.clientX - translateX;
                    startY = e.clientY - translateY;
                    img.style.cursor = 'grabbing';
                }
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                
                img.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
            });
            
            document.addEventListener('mouseup', () => {
                isDragging = false;
                img.style.cursor = scale > 1 ? 'grab' : 'zoom-out';
            });
            
            mediaContainer.appendChild(img);
        } 
        else if (item.type === 'video') {
            const video = document.createElement('video');
            video.src = item.url;
            video.controls = false;
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.className = 'object-contain cursor-zoom-out mt-20';
            

            video.style.maxWidth = '80vw';
            video.style.maxHeight = '80vh';

            // Optional: Add border or padding for nicer display
            video.style.borderRadius = '8px';
            video.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';



            // Show custom video controls
            const videoControls = document.getElementById(`video-controls-${propertyId}`);
            videoControls.classList.remove('hidden');
            
            // Set up video controls
            const playPauseBtn = document.getElementById(`play-pause-${propertyId}`);
            const progressBar = document.getElementById(`progress-bar-${propertyId}`);
            const currentTimeEl = document.getElementById(`current-time-${propertyId}`);
            const durationEl = document.getElementById(`duration-${propertyId}`);
            const muteBtn = document.getElementById(`mute-${propertyId}`);
            const fullscreenBtn = document.getElementById(`fullscreen-video-${propertyId}`);
            
            // Update time display
            const formatTime = (seconds) => {
                const mins = Math.floor(seconds / 60);
                const secs = Math.floor(seconds % 60);
                return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
            };
            
            video.addEventListener('loadedmetadata', () => {
                durationEl.textContent = formatTime(video.duration);
            });
            
            video.addEventListener('timeupdate', () => {
                const progress = (video.currentTime / video.duration) * 100;
                progressBar.style.width = `${progress}%`;
                currentTimeEl.textContent = formatTime(video.currentTime);
            });
            
            // Click on progress bar to seek
            const progressContainer = progressBar.parentElement;
            progressContainer.addEventListener('click', (e) => {
                const rect = progressContainer.getBoundingClientRect();
                const pos = (e.clientX - rect.left) / rect.width;
                video.currentTime = pos * video.duration;
            });
            
            // Play/Pause toggle
            playPauseBtn.addEventListener('click', () => {
                if (video.paused) {
                    video.play();
                    playPauseBtn.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                        </svg>
                    `;
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                        </svg>
                    `;
                }
            });
            
            // Mute toggle
            muteBtn.addEventListener('click', () => {
                video.muted = !video.muted;
                muteBtn.innerHTML = video.muted ? `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                    </svg>
                ` : `
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z" clip-rule="evenodd" />
                    </svg>
                `;
            });
            
            // Fullscreen toggle
            fullscreenBtn.addEventListener('click', () => {
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                } else if (video.msRequestFullscreen) {
                    video.msRequestFullscreen();
                }
            });
            
            mediaContainer.appendChild(video);
        }
        
        elements.fullscreenPreview.appendChild(mediaContainer);
    }
    



    
    function closeFullscreenHandler() {
        // Hide video controls if visible
        const videoControls = document.getElementById(`video-controls-${propertyId}`);
        if (videoControls) videoControls.classList.add('hidden');
        
        elements.fullscreenModal.classList.add('hidden');
        document.body.style.overflow = '';
        document.documentElement.style.overflow = '';
        
        // Pause any playing video
        const videos = elements.fullscreenPreview.querySelectorAll('video');
        videos.forEach(video => {
            video.pause();
            video.currentTime = 0;
        });
    }



    // Navigate between media items
    function navigateMedia(direction) {
        const newIndex = currentIndex + direction;
        
        if (newIndex >= 0 && newIndex < mediaItems.length) {
            currentIndex = newIndex;
            updateGallery();
            scrollThumbnailIntoView();
        }
    }

    // Scroll active thumbnail into view
    function scrollThumbnailIntoView() {
        const activeThumb = elements.mediaThumbnails.querySelector(`button[data-index="${currentIndex}"]`);
        if (activeThumb) {
            activeThumb.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }

    // Update thumbnail navigation arrows visibility
    function updateThumbnailArrows() {
        if (mediaItems.length === 0) {
            elements.thumbPrev.classList.add('hidden');
            elements.thumbNext.classList.add('hidden');
            return;
        }
        
        elements.thumbPrev.classList.toggle('hidden', currentIndex === 0);
        elements.thumbNext.classList.toggle('hidden', currentIndex === mediaItems.length - 1);
    }

    // Setup thumbnail navigation
    function setupThumbnailNavigation() {
        updateThumbnailArrows();
        
        elements.thumbPrev.addEventListener('click', (e) => {
            e.preventDefault();
            navigateMedia(-1);
        });
        
        elements.thumbNext.addEventListener('click', (e) => {
            e.preventDefault();
            navigateMedia(1);
        });
    }

    // Setup event listeners
    function setupEventListeners() {
        // Thumbnail click handlers
        document.querySelectorAll(`#media-thumbnails-${propertyId} button, #fullscreen-thumbnails-${propertyId} button`).forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                currentIndex = parseInt(btn.getAttribute('data-index'));
                updateGallery();
            });
        });
        
        // Fullscreen navigation
        elements.fsPrev.addEventListener('click', (e) => {
            e.preventDefault();
            navigateMedia(-1);
        });
        
        elements.fsNext.addEventListener('click', (e) => {
            e.preventDefault();
            navigateMedia(1);
        });
        
        // Close fullscreen
        elements.closeFullscreen.addEventListener('click', closeFullscreenHandler);
        elements.fullscreenModal.addEventListener('click', (e) => {
            if (e.target === elements.fullscreenModal) {
                closeFullscreenHandler();
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (elements.fullscreenModal.classList.contains('hidden')) return;
            
            switch (e.key) {
                case 'Escape':
                    closeFullscreenHandler();
                    break;
                case 'ArrowUp':
                    navigateMedia(-1);
                    break;
                case 'ArrowDown':
                    navigateMedia(1);
                    break;
            }
        });
    }

    // Initialize the gallery
    initGallery();
}