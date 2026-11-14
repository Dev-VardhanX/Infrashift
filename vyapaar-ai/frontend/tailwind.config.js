/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 50: "#fff7ed", 100: "#ffedd5", 500: "#f97316", 600: "#ea580c", 700: "#c2410c" },
        ink: { 900: "#1c1917", 700: "#44403c", 500: "#78716c", 200: "#e7e5e4", 100: "#f5f5f4" },
      },
      fontFamily: { sans: ["Inter", "system-ui", "Segoe UI", "Noto Sans Devanagari", "sans-serif"] },
    },
  },
  plugins: [],
};
