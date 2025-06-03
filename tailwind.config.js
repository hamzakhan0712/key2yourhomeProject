/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',            // Global Django templates
    './**/templates/**/*.html',         // App-specific Django templates
    './node_modules/flowbite/**/*.js',   // Required for Flowbite components
    './static/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        // Make sure red is included
        red: colors.red,
      }
    },
  },
   // Add safelist for colors you want to keep
   safelist: [
    'text-red-500',
    'bg-red-500',
    // other colors you need
  ],
  plugins: [
    require('flowbite/plugin')          // Load Flowbite plugin
  ],
};
