/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'listen': 'listen 1s ease-in-out infinite',
        'think': 'think 2s ease-in-out infinite',
        'speak': 'speak 0.5s ease-in-out infinite',
        'sound-wave': 'soundWave 0.6s ease-in-out infinite alternate',
        'breathe': 'breathe 4s ease-in-out infinite',
        'blink': 'blink 4s ease-in-out infinite',
        'nod': 'nod 0.5s ease-in-out',
        'mouth-speak': 'mouthSpeak 0.3s ease-in-out infinite alternate',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        listen: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
        think: {
          '0%, 100%': { transform: 'rotate(-2deg)' },
          '50%': { transform: 'rotate(2deg)' },
        },
        speak: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        soundWave: {
          '0%': { height: '20%' },
          '100%': { height: '100%' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        blink: {
          '0%, 45%, 55%, 100%': { transform: 'scaleY(1)' },
          '50%': { transform: 'scaleY(0.1)' },
        },
        nod: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(3px)' },
        },
        mouthSpeak: {
          '0%': { transform: 'scaleY(1)' },
          '100%': { transform: 'scaleY(1.3)' },
        },
      },
    },
  },
  plugins: [],
}
