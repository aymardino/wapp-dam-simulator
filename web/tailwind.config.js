/** Système de design : palette neutre chaude, un accent vert, en-tête sombre, deux poids de police. */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        page: '#F4F4F0',
        surface: '#FFFFFF',
        panel: '#F7F7F4',
        brand: { DEFAULT: '#0B3D30', 2: '#0F4A3A', ink: '#D7E8E1' },
        ink: { DEFAULT: '#1B1B19', 2: '#5C5B56', 3: '#8C8B84' },
        line: { DEFAULT: '#E2E0D9', strong: '#C8C6BE' },
        accent: { DEFAULT: '#0F6E56', hover: '#0C5A46', soft: '#E1F5EE', ink: '#085041' },
        up: { DEFAULT: '#2F6A0E', soft: '#EAF3DE' },
        down: { DEFAULT: '#A32D2D', soft: '#FCEBEB' },
        warn: { DEFAULT: '#854F0B', soft: '#FAEEDA' },
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'], mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'] },
      fontSize: { xs: ['12px', '16px'], sm: ['13.5px', '18px'], base: ['15px', '22px'], lg: ['17px', '24px'], xl: ['22px', '28px'], '2xl': ['28px', '34px'], '3xl': ['34px', '40px'] },
      borderRadius: { DEFAULT: '8px', lg: '12px' },
      boxShadow: { panel: '0 1px 2px rgba(27,27,25,0.04)' },
    },
  },
  plugins: [],
}
