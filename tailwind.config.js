module.exports = {
  content: [
    "./**/*.html",
    "./**/*.js",
    "./**/*.py"
  ],
  safelist: [
    "bg-sky-50","border-sky-200",
    "bg-emerald-50","border-emerald-200",
    "bg-amber-50","border-amber-200",
    "bg-rose-50","border-rose-200",
    "bg-violet-50","border-violet-200",
    "bg-indigo-50","border-indigo-200",
    // bullets/carrousel générées dynamiquement
    "swiper-pagination-bullet","swiper-pagination-bullet-active"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#E3F2FD",
          100: "#d6ecfb",
          200: "#b6dbf7",
          300: "#90c7f2",
          400: "#64aeea",
          500: "#3f91db",
          600: "#12475b",   // bleu institutionnel (navbar)
          700: "#0f3a47",   // hover/actif
          800: "#0b2f38",
          900: "#081f26",
          DEFAULT: "#12475b"
        },
        // Jaune CTA fort
        cta: {
          500: "#FFC400",
          600: "#E0B000",
          700: "#CC9F00",
          DEFAULT: "#FFC400"
        },
        // Vert "Kit personnalisé"
        kit: {
          DEFAULT: "#00cc66",  // custom kit button color
          600: "#00b359",
          700: "#00964c"
        },
        ink: "#263238"
      },
      borderRadius: { "2xl": "1rem" }
    }
  },
  plugins: [],
};
