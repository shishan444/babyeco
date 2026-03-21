/**
 * BabyEco Design System - Tailwind CSS Configuration
 * Unified design tokens for Child and Parent applications
 *
 * @version 1.0.0
 * @last-updated 2026-03-21
 */

module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    './pages/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],

  theme: {
    extend: {
      colors: {
        /* ============================================
           CHILD APP COLORS
           ============================================ */
        child: {
          primary: {
            DEFAULT: '#FF6B6B',
            light: '#FF8B8B',
            dark: '#E55555',
          },
          secondary: {
            DEFAULT: '#4ECDC4',
            light: '#6ED9D2',
            dark: '#3CB8AF',
          },
          accent: '#FFE66D',
          success: '#95E1A3',
          warning: '#FFD93D',
          danger: '#FF8B94',
          bg: {
            primary: '#FFF9F0',
            secondary: '#FFFFFF',
            overlay: 'rgba(0, 0, 0, 0.4)',
            hover: 'rgba(255, 107, 107, 0.08)',
          },
          text: {
            primary: '#2D3436',
            secondary: '#636E72',
            muted: '#B2BEC3',
            inverse: '#FFFFFF',
          },
        },

        /* ============================================
           PARENT APP COLORS
           ============================================ */
        parent: {
          primary: {
            DEFAULT: '#4F46E5',
            light: '#6366F1',
            dark: '#4338CA',
          },
          secondary: {
            DEFAULT: '#7C3AED',
            light: '#8B5CF6',
            dark: '#6D28D9',
          },
          bg: {
            primary: '#F9FAFB',
            secondary: '#FFFFFF',
            overlay: 'rgba(0, 0, 0, 0.5)',
            hover: 'rgba(79, 70, 229, 0.08)',
          },
          text: {
            primary: '#111827',
            secondary: '#6B7280',
            muted: '#9CA3AF',
            inverse: '#FFFFFF',
          },
        },

        /* ============================================
           SEMANTIC COLORS (Shared)
           ============================================ */
        success: {
          DEFAULT: '#10B981',
          light: '#D1FAE5',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FEF3C7',
          dark: '#D97706',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#FEE2E2',
          dark: '#DC2626',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#DBEAFE',
          dark: '#2563EB',
        },

        /* ============================================
           GRAY SCALE
           ============================================ */
        gray: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
          950: '#0B0F19',
        },
      },

      fontFamily: {
        display: ['Nunito', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        body: ['Nunito', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },

      fontSize: {
        /* Child App - Larger base sizes */
        'child-xs': ['0.75rem', { lineHeight: '1rem', fontWeight: '500' }],
        'child-sm': ['0.875rem', { lineHeight: '1.25rem', fontWeight: '600' }],
        'child-base': ['1rem', { lineHeight: '1.5rem', fontWeight: '600' }],
        'child-lg': ['1.125rem', { lineHeight: '1.75rem', fontWeight: '600' }],
        'child-xl': ['1.25rem', { lineHeight: '1.75rem', fontWeight: '700' }],
        'child-2xl': ['1.5rem', { lineHeight: '2rem', fontWeight: '700' }],
        'child-3xl': ['2rem', { lineHeight: '2.5rem', fontWeight: '800' }],
        'child-4xl': ['2.5rem', { lineHeight: '3rem', fontWeight: '800' }],

        /* Parent App - Standard sizes */
        'parent-xs': ['0.75rem', { lineHeight: '1rem' }],
        'parent-sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'parent-base': ['1rem', { lineHeight: '1.5rem' }],
        'parent-lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'parent-xl': ['1.25rem', { lineHeight: '1.75rem' }],
        'parent-2xl': ['1.5rem', { lineHeight: '2rem' }],
        'parent-3xl': ['2rem', { lineHeight: '2.5rem' }],
        'parent-4xl': ['2.5rem', { lineHeight: '3rem' }],
      },

      fontWeight: {
        medium: '500',
        semibold: '600',
        extrabold: '800',
      },

      spacing: {
        '18': '4.5rem',   /* 72px */
        '22': '5.5rem',   /* 88px */
        '26': '6.5rem',   /* 104px */
        '28': '7rem',     /* 112px */
        '30': '7.5rem',   /* 120px */
        '36': '9rem',     /* 144px */
        '44': '11rem',    /* 176px */
        '52': '13rem',    /* 208px */
        '56': '14rem',    /* 224px */
        '60': '15rem',    /* 240px */
        '64': '16rem',    /* 256px */
        '72': '18rem',    /* 288px */
        '80': '20rem',    /* 320px */
        '96': '24rem',    /* 384px */
      },

      borderRadius: {
        '4xl': '2rem',
      },

      boxShadow: {
        /* Child App - Softer shadows */
        'child-sm': '0 2px 4px rgba(0, 0, 0, 0.05)',
        'child-md': '0 4px 8px rgba(0, 0, 0, 0.08)',
        'child-lg': '0 8px 16px rgba(0, 0, 0, 0.1)',
        'child-xl': '0 12px 24px rgba(0, 0, 0, 0.12)',
      },

      zIndex: {
        dropdown: '100',
        sticky: '200',
        fixed: '300',
        'modal-backdrop': '400',
        modal: '500',
        popover: '600',
        tooltip: '700',
      },

      transitionDuration: {
        '75': '75ms',
        '700': '700ms',
        '1000': '1000ms',
      },

      transitionTimingFunction: {
        bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      },

      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        fadeOut: {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        slideUp: {
          from: { transform: 'translateY(16px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          from: { transform: 'translateY(-16px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          from: { transform: 'scale(0.95)', opacity: '0' },
          to: { transform: 'scale(1)', opacity: '1' },
        },
        confetti: {
          '0%': { transform: 'translateY(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'translateY(-100px) rotate(720deg)', opacity: '0' },
        },
        pointsFloat: {
          '0%': { transform: 'translateY(0) scale(1)', opacity: '1' },
          '50%': { transform: 'translateY(-30px) scale(1.2)', opacity: '1' },
          '100%': { transform: 'translateY(-60px) scale(0.8)', opacity: '0' },
        },
        trophyBounce: {
          '0%': { transform: 'scale(0.5) rotate(-10deg)' },
          '50%': { transform: 'scale(1.2) rotate(10deg)' },
          '100%': { transform: 'scale(1) rotate(0deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },

      animation: {
        fadeIn: 'fadeIn 200ms ease-out',
        fadeOut: 'fadeOut 200ms ease-out',
        slideUp: 'slideUp 300ms ease-out',
        slideDown: 'slideDown 300ms ease-out',
        scaleIn: 'scaleIn 200ms ease-out',
        confetti: 'confetti 1.5s ease-out',
        pointsFloat: 'pointsFloat 1s ease-out',
        trophyBounce: 'trophyBounce 600ms ease-out',
        shimmer: 'shimmer 2s infinite linear',
      },

      screens: {
        xs: '480px',
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',
      },
    },
  },

  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
