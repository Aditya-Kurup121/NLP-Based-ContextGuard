/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#070a12',
          900: '#0b0f19',
          850: '#0f172a',
          800: '#131e36',
          700: '#1e293b',
          600: '#334155',
        },
        accent: {
          teal: '#14b8a6',
          cyan: '#06b6d4',
          violet: '#8b5cf6',
          indigo: '#6366f1',
        },
        risk: {
          low: '#10b981',      // Green - Friendly Banter / Neutral
          moderate: '#f59e0b', // Amber/Yellow - Ambiguous / Potentially Harmful
          high: '#f97316',     // Orange - Concerning / Possible Cyberbullying
          critical: '#ef4444', // Red - Threat / Severe Concern
          uncertain: '#94a3b8' // Gray - More Context Needed
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace']
      }
    },
  },
  plugins: [],
}
