/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './dashboard/**/*.py',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        charcoal: {
          DEFAULT: '#16181C',
        },
        graphite: {
          DEFAULT: '#23262C',
        },
        steel: {
          DEFAULT: '#3A3F47',
        },
        safety: {
          DEFAULT: '#F26A1B',
          hover: '#D95B12',
        },
        brass: {
          DEFAULT: '#B8914A',
          light: '#EFE6D2',
          dark: '#6E5420',
        },
        bone: {
          DEFAULT: '#F4F1EA',
        },
        line: {
          DEFAULT: '#E3DED3',
        },
        muted: {
          DEFAULT: '#6B7380',
        },
        go: {
          DEFAULT: '#3E8E5A',
          light: '#EAF5EE',
        },
        danger: {
          DEFAULT: '#B23A3A',
          light: '#FDF2F2',
        },
      },
      fontFamily: {
        display: ['"Plus Jakarta Sans"', '"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        body: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        full: '9999px',
      },
      boxShadow: {
        none: 'none',
      },
    },
  },
  plugins: [],
}
