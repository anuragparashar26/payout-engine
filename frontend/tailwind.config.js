/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        accent: {
          blue: '#2563eb',
          'blue-hover': '#1d4ed8',
          'blue-light': '#3b82f6',
          black: '#0f172a',
          'black-hover': '#1e293b',
        },
      },
      backgroundImage: {
        'gradient-premium': 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
        'gradient-card': 'linear-gradient(145deg, rgba(30, 30, 30, 0.8) 0%, rgba(10, 10, 10, 0.9) 100%)',
        'gradient-header': 'linear-gradient(135deg, rgba(37, 99, 235, 0.12) 0%, rgba(15, 23, 42, 0.8) 50%, rgba(37, 99, 235, 0.08) 100%)',
        'gradient-button': 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
        'gradient-button-hover': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        'gradient-blue': 'linear-gradient(135deg, rgba(37, 99, 235, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%)',
      },
    },
  },
  plugins: [],
}