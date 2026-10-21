const v = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

module.exports = {
  darkMode: ['selector', '[data-theme="dark"]'],
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Theme-aware (values change in dark mode, see globals.css)
        ink: v('ink'),           // text
        graphite: v('graphite'), // secondary text
        ash: v('ash'),           // muted text
        fog: v('fog'),           // hairlines
        mist: v('mist'),         // quiet fills
        line: v('line'),         // control borders
        white: v('surface'),     // "white" surfaces become dark surfaces in dark mode
        canvas: v('canvas'),     // chat / editor background
        accent: v('accent'),     // links and accent text
        // Fixed (same in both themes)
        onaccent: '#ffffff',     // text on gradient / accent fills
        periwinkle: { DEFAULT: '#8da2f0', deep: '#4f63d2' },
        lavender: '#b9a8ee',
        sky: '#a8dcea',
        butter: '#f4e58c',
        blush: '#f5b5c0',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
        lift: 'var(--shadow-lift)',
      },
      keyframes: {
        'chat-in': { '0%': { opacity: '0', transform: 'translateY(18px) scale(0.94)' }, '100%': { opacity: '1', transform: 'translateY(0) scale(1)' } },
        'chat-out': { '0%': { opacity: '1', transform: 'translateY(0) scale(1)' }, '100%': { opacity: '0', transform: 'translateY(18px) scale(0.94)' } },
        'pop-in': { '0%': { opacity: '0', transform: 'translateY(-6px) scale(0.96)' }, '100%': { opacity: '1', transform: 'translateY(0) scale(1)' } },
        'fade-up': { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        'draw-line': { '0%': { transform: 'scaleY(0)' }, '100%': { transform: 'scaleY(1)' } },
        'ping-soft': { '0%': { transform: 'scale(1)', opacity: '0.45' }, '80%, 100%': { transform: 'scale(1.7)', opacity: '0' } },
      },
      animation: {
        'chat-in': 'chat-in 260ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'chat-out': 'chat-out 200ms cubic-bezier(0.55, 0, 0.55, 0.2) both',
        'pop-in': 'pop-in 160ms ease-out both',
        'fade-up': 'fade-up 420ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'draw-line': 'draw-line 900ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'ping-soft': 'ping-soft 2.4s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
    },
  },
  plugins: [],
};
