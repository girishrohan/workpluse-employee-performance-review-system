const path = require('path');

module.exports = {
  content: [
    path.resolve(__dirname, 'src-frontend', 'index.html'),
    path.resolve(__dirname, 'src-frontend', 'src', '**/*.{ts,tsx}'),
    path.resolve(__dirname, 'index.html'),
  ],
  theme: {
    extend: {
      colors: {
        teal: {
          50: '#f0fdfa',
          100: '#dcc1a0',
          200: '#93f4ed',
          300: '#55e8e1',
          400: '#24d8ca',
          500: '#168c83',
          600: '#0e7c7b',
          700: '#0e685a',
          800: '#154f3d',
          900: '#1d3b2e',
        },
        navy: {
          50: '#f0f4f8',
          100: '#e2eaf5',
          200: '#cdd6ea',
          300: '#a9c1db',
          400: '#6793c9',
          500: '#3068ae',
          600: '#1a4a78',
          700: '#102a43',
          800: '#0c2432',
          900: '#081724',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
      },
      animation: {
        'spin': 'spin 1s linear infinite',
      },
      keyframes: {
        spin: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
      },
    },
  },
  plugins: [],
};