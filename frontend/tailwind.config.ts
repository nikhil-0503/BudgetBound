import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    colors: {
      // Grays (from Tailwind)
      slate: {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a',
      },
      
      // NEW DARK THEME - Custom palette
      black: {
        primary: '#050505',      // Near-black - page background
        secondary: '#080B14',    // Very dark - elevated surfaces
        tertiary: '#0B1020',     // Dark navy-black - cards
        quaternary: '#0D1224',   // Dark navy - alternate card background
        DEFAULT: '#000000',
      },
      
      // Dark navy accents for hierarchy
      'dark-navy': {
        DEFAULT: '#10162A',      // Very dark blue
        light: '#111827',        // Slightly lighter dark navy
      },
      
      // Borders
      border: {
        dark: '#1E293B',         // Subtle dark blue-gray
        subtle: '#26324A',       // Even more subtle
      },
      
      // Text colors (light for dark backgrounds)
      text: {
        primary: '#F8FAFC',      // Nearly white - primary text
        secondary: '#CBD5E1',    // Light gray - secondary text
        muted: '#94A3B8',        // Muted gray - tertiary text
      },
      
      // Blue accents (primary interactive)
      blue: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
        accent: '#3B82F6',
        'accent-light': '#60A5FA',
        'accent-dark': '#1E40AF',
      },
      
      // Pink accents (secondary interactive)
      pink: {
        50: '#fdf2f8',
        100: '#fce7f3',
        200: '#fbcfe8',
        300: '#f8b4d1',
        400: '#f472b6',
        500: '#ec4899',
        600: '#db2777',
        700: '#be185d',
        800: '#9d174d',
        900: '#831843',
        accent: '#EC4899',
        'accent-light': '#F472B6',
        'accent-dark': '#BE185D',
      },
      
      // Supporting colors
      emerald: {
        500: '#10b981',
        600: '#059669',
      },
      red: {
        500: '#ef4444',
        600: '#dc2626',
      },
      amber: {
        500: '#f59e0b',
        600: '#d97706',
      },
      cyan: {
        500: '#06b6d4',
        600: '#0891b2',
      },
      purple: {
        500: '#a855f7',
        600: '#9333ea',
      },
      white: '#ffffff',
      transparent: 'transparent',
    },
    extend: {
      backgroundImage: {
        'gradient-blue-pink': 'linear-gradient(to right, #3B82F6, #EC4899)',
        'gradient-blue-pink-dark': 'linear-gradient(to right, #60A5FA, #F472B6)',
      },
      boxShadow: {
        'blue-glow': '0 0 20px rgba(59, 130, 246, 0.3)',
        'pink-glow': '0 0 20px rgba(236, 72, 153, 0.3)',
        'blue-pink-glow': '0 0 30px rgba(59, 130, 246, 0.2), 0 0 30px rgba(236, 72, 153, 0.2)',
      },
    },
  },
  plugins: [],
};

export default config;
