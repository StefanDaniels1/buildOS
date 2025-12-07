/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'buildos': {
          'primary': '#0696D7',
          'secondary': '#5BC3E8',
          'dark': '#1a1a2e',
          'darker': '#0f0f1a',
          // Light mode colors
          'light': '#ffffff',
          'light-secondary': '#f8fafc',
          'light-tertiary': '#f1f5f9',
        }
      }
    },
  },
  plugins: [],
}
