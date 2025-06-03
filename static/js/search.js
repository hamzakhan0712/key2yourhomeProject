// // static/js/search.js
// document.addEventListener('DOMContentLoaded', function() {
//   // Initialize all search interfaces
//   const searchSystem = new RealEstateSearch({
//     searchUrl: '/search/',
//     minChars: 2,
//     debounceDelay: 300
//   });

//   // Initialize mobile search toggle
//   document.getElementById('mobile-search-toggle').addEventListener('click', function() {
//     const search = document.getElementById('mobile-search');
//     search.classList.toggle('hidden');
//     document.getElementById('mobile-menu').classList.add('hidden');
    
//     // Focus on input when mobile search is shown
//     if (!search.classList.contains('hidden')) {
//       search.querySelector('input').focus();
//     }
//   });

//   // Initialize amenities dropdown
//   const amenitiesToggle = document.getElementById('amenities-toggle');
//   if (amenitiesToggle) {
//     amenitiesToggle.addEventListener('click', function() {
//       document.getElementById('amenities-dropdown').classList.toggle('hidden');
//     });

//     // Close amenities dropdown when clicking outside
//     document.addEventListener('click', function(e) {
//       if (!amenitiesToggle.contains(e.target) && 
//           !document.getElementById('amenities-dropdown').contains(e.target)) {
//         document.getElementById('amenities-dropdown').classList.add('hidden');
//       }
//     });
//   }

//   // Clear recent searches
//   const clearRecentSearches = document.getElementById('clear-recent-searches');
//   if (clearRecentSearches) {
//     clearRecentSearches.addEventListener('click', function() {
//       localStorage.removeItem('recentSearches');
//       document.getElementById('mobile-recent-searches').innerHTML = `
//         <div class="px-3 py-2 bg-white rounded-lg text-sm text-gray-500">
//           No recent searches
//         </div>
//       `;
//     });
//   }
// });



// // static/js/search.js
// class RealEstateSearch {
//     constructor(options) {
//       this.searchUrl = options.searchUrl || '/search/';
//       this.minChars = options.minChars || 2;
//       this.debounceDelay = options.debounceDelay || 300;
//       this.searchType = options.searchType || 'property'; // Default to property search
      
//       // Initialize all search interfaces
//       this.initLandingSearch();
//       this.initNavbarSearch();
//       this.initMobileSearch();
      
//       // Recent searches from localStorage
//       this.recentSearches = JSON.parse(localStorage.getItem('recentSearches') || []);
//     }
  
//     initLandingSearch() {
//       const form = document.getElementById('property-search-form');
//       if (!form) return;
      
//       form.addEventListener('submit', (e) => {
//         e.preventDefault();
//         this.submitSearch(form, 'property');
//       });
      
//       // Add event listeners for other form elements as needed
//     }
  
//     initNavbarSearch() {
//       const searchInput = document.getElementById('desktop-search-input');
//       const searchResults = document.getElementById('desktop-search-results');
//       const searchType = document.getElementById('search-type');
      
//       if (!searchInput || !searchResults) return;
      
//       // Set search type from dropdown
//       this.searchType = searchType.value;
//       searchType.addEventListener('change', () => {
//         this.searchType = searchType.value;
//       });
      
//       searchInput.addEventListener('input', this.debounce(() => {
//         this.handleSearchInput(searchInput, searchResults);
//       }, this.debounceDelay));
      
//       searchInput.addEventListener('focus', () => {
//         this.showRecentSearches(searchResults);
//       });
      
//       // Hide results when clicking outside
//       document.addEventListener('click', (e) => {
//         if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
//           searchResults.classList.add('hidden');
//         }
//       });
//     }
  
//     initMobileSearch() {
//       const mobileSearch = document.getElementById('mobile-search');
//       if (!mobileSearch) return;
      
//       const input = mobileSearch.querySelector('input');
//       input.addEventListener('input', this.debounce(() => {
//         this.handleMobileSearchInput(input);
//       }, this.debounceDelay));
//     }
  
//     handleSearchInput(input, resultsContainer) {
//       const query = input.value.trim();
      
//       if (query.length < this.minChars) {
//         this.showRecentSearches(resultsContainer);
//         return;
//       }
      
//       fetch(`${this.searchUrl}?q=${encodeURIComponent(query)}&type=${this.searchType}`, {
//         headers: { 'X-Requested-With': 'XMLHttpRequest' }
//       })
//       .then(response => response.json())
//       .then(data => {
//         this.displaySearchResults(data, resultsContainer);
//       });
//     }
  
//     displaySearchResults(data, container) {
//       // Clear previous results
//       container.innerHTML = '';
      
//       // Show matching results
//       const resultsSection = document.createElement('div');
//       resultsSection.className = 'py-2';
      
//       if (data.results.length > 0) {
//         const heading = document.createElement('div');
//         heading.className = 'px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider';
//         heading.textContent = 'Matching Properties';
//         resultsSection.appendChild(heading);
        
//         const list = document.createElement('ul');
//         list.className = 'text-sm text-gray-700';
        
//         data.results.forEach(result => {
//           const item = document.createElement('li');
//           item.innerHTML = `
//             <a href="/${result.type}/${result.id}" class="block px-4 py-3 hover:bg-blue-50 flex items-center">
//               <div class="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-md overflow-hidden mr-3">
//                 <img src="/media/${result.image || 'default.jpg'}" class="h-full w-full object-cover">
//               </div>
//               <div>
//                 <div class="font-medium text-gray-900">${result.name}</div>
//                 <div class="text-xs text-gray-500">${result.city}</div>
//               </div>
//             </a>
//           `;
//           list.appendChild(item);
//         });
        
//         resultsSection.appendChild(list);
//       }
      
//       // Show suggestions if available
//       if (data.suggestions.length > 0) {
//         const suggestionsSection = document.createElement('div');
//         suggestionsSection.className = 'py-2 border-t border-gray-100';
        
//         const heading = document.createElement('div');
//         heading.className = 'px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider';
//         heading.textContent = 'Suggestions';
//         suggestionsSection.appendChild(heading);
        
//         const suggestionsDiv = document.createElement('div');
//         suggestionsDiv.className = 'px-3';
        
//         const suggestionsList = document.createElement('div');
//         suggestionsList.className = 'flex flex-wrap gap-2';
        
//         data.suggestions.forEach(suggestion => {
//           const tag = document.createElement('a');
//           tag.href = `${this.searchUrl}?q=${encodeURIComponent(suggestion)}&type=${this.searchType}`;
//           tag.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 hover:bg-gray-200';
//           tag.textContent = suggestion;
//           suggestionsList.appendChild(tag);
//         });
        
//         suggestionsDiv.appendChild(suggestionsList);
//         suggestionsSection.appendChild(suggestionsDiv);
//         container.appendChild(suggestionsSection);
//       }
      
//       container.appendChild(resultsSection);
//       container.classList.remove('hidden');
//     }
  
//     showRecentSearches(container) {
//       // Clear previous results
//       container.innerHTML = '';
      
//       const recentSection = document.createElement('div');
//       recentSection.className = 'py-2';
      
//       const heading = document.createElement('div');
//       heading.className = 'px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider flex justify-between items-center';
      
//       const title = document.createElement('span');
//       title.textContent = 'Recent Searches';
      
//       const clearBtn = document.createElement('button');
//       clearBtn.className = 'text-xs text-blue-600 hover:text-blue-800';
//       clearBtn.textContent = 'Clear All';
//       clearBtn.addEventListener('click', () => {
//         this.clearRecentSearches();
//         container.classList.add('hidden');
//       });
      
//       heading.appendChild(title);
//       heading.appendChild(clearBtn);
//       recentSection.appendChild(heading);
      
//       if (this.recentSearches.length > 0) {
//         const list = document.createElement('ul');
//         list.className = 'text-sm text-gray-700';
        
//         this.recentSearches.slice(0, 5).forEach(search => {
//           const item = document.createElement('li');
//           item.innerHTML = `
//             <a href="${search.url}" class="block px-4 py-2 hover:bg-blue-50 flex items-center justify-between">
//               <span class="flex items-center">
//                 <svg class="h-4 w-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
//                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
//                 </svg>
//                 ${search.query}
//               </span>
//               <span class="text-xs text-gray-400">${search.time}</span>
//             </a>
//           `;
//           list.appendChild(item);
//         });
        
//         recentSection.appendChild(list);
//       } else {
//         const emptyMsg = document.createElement('div');
//         emptyMsg.className = 'px-4 py-2 text-sm text-gray-500';
//         emptyMsg.textContent = 'No recent searches';
//         recentSection.appendChild(emptyMsg);
//       }
      
//       container.appendChild(recentSection);
//       container.classList.remove('hidden');
//     }
  
//     clearRecentSearches() {
//       this.recentSearches = [];
//       localStorage.setItem('recentSearches', JSON.stringify(this.recentSearches));
//     }
  
//     addRecentSearch(query, url) {
//       // Avoid duplicates
//       this.recentSearches = this.recentSearches.filter(s => s.query !== query);
      
//       // Add new search
//       this.recentSearches.unshift({
//         query: query,
//         url: url,
//         time: new Date().toLocaleDateString(),
//       });
      
//       // Keep only last 10 searches
//       if (this.recentSearches.length > 10) {
//         this.recentSearches = this.recentSearches.slice(0, 10);
//       }
      
//       localStorage.setItem('recentSearches', JSON.stringify(this.recentSearches));
//     }
  
//     submitSearch(form, searchType) {
//       const formData = new FormData(form);
//       const queryParams = new URLSearchParams();
      
//       // Add all form data to query params
//       formData.forEach((value, key) => {
//         if (value) queryParams.append(key, value);
//       });
      
//       // Add search type
//       queryParams.append('type', searchType);
      
//       // Add to recent searches
//       const query = formData.get('location') || formData.get('q') || '';
//       if (query) {
//         this.addRecentSearch(query, `/search/?${queryParams.toString()}`);
//       }
      
//       // Submit the form
//       window.location.href = `/search/?${queryParams.toString()}`;
//     }
  
//     debounce(func, wait) {
//       let timeout;
//       return function executedFunction(...args) {
//         const later = () => {
//           clearTimeout(timeout);
//           func(...args);
//         };
//         clearTimeout(timeout);
//         timeout = setTimeout(later, wait);
//       };
//     }
//   }
  
//   // Initialize when DOM is loaded
//   document.addEventListener('DOMContentLoaded', () => {
//     window.realEstateSearch = new RealEstateSearch({
//       searchUrl: '/search/',
//       minChars: 2,
//       debounceDelay: 300
//     });
//   });