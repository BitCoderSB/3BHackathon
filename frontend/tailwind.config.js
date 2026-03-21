/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
      },
      fontSize: {
        'dense-xs': ['12px', { lineHeight: '16px' }],
        'dense-sm': ['13px', { lineHeight: '18px' }],
        'dense-base': ['14px', { lineHeight: '20px' }],
      },
      letterSpacing: {
        'heading': '-0.025em',
        'label': '0.075em',
      },
      colors: {
        brand: {
          red: "#e20a19",
          dark: "#b80813",
          light: "#fef2f2",
        },
        surface: {
          page: "#F5F5F7",
          card: "#FFFFFF",
          muted: "#F9FAFB",
        },
        status: {
          green: "#22C55E",
          yellow: "#F59E0B",
          red: "#EF4444",
          blue: "#3B82F6",
        },
        heatmap: {
          cool: "#3B82F6",
          warm: "#F59E0B",
          hot: "#EF4444",
        },
        critical: "#DC2626",
      },
      spacing: {
        'grid-gap': '16px',
        'card-pad': '12px',
      },
      borderRadius: {
        'bento': '24px',
      },
      boxShadow: {
        'bento': '0 4px 6px rgba(0,0,0,0.05)',
        'bento-hover': '0 12px 28px rgba(0,0,0,0.08), 0 4px 10px rgba(0,0,0,0.04)',
        'bento-active': '0 2px 4px rgba(0,0,0,0.06)',
      },
      keyframes: {
        'pulse-live': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'count-up': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'pulse-live': 'pulse-live 2s ease-in-out infinite',
        'slide-in': 'slide-in 0.3s ease-out',
        'count-up': 'count-up 0.4s ease-out',
      },
    },
  },
  plugins: [],
};
