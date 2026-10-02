/** Système de design : palette neutre, un seul accent, deux poids de police. */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        page: '#F6F6F3',
        surface: '#FFFFFF',
        panel: '#F0F0EC',
        ink: { DEFAULT: '#1A1A18', 2: '#5F5E5A', 3: '#8A8983' },
        line: { DEFAULT: '#E4E2DC', strong: '#C9C7C0' },
        accent: { DEFAULT: '#0F6E56', soft: '#E1F5EE', ink: '#085041' },
        up: { DEFAULT: '#3B6D11', soft: '#EAF3DE' },
        down: { DEFAULT: '#A32D2D', soft: '#FCEBEB' },
        warn: { DEFAULT: '#854F0B', soft: '#FAEEDA' },
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'], mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
      fontSize: { xs: ['12px', '16px'], sm: ['13px', '18px'], base: ['14px', '20px'], lg: ['16px', '22px'], xl: ['20px', '26px'], '2xl': ['26px', '32px'] },
      borderRadius: { DEFAULT: '6px', lg: '10px' },
    },
  },
  plugins: [],
}
