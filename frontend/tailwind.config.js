/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        soc: {
          bg: "#0b0f19",
          card: "#131b2e",
          border: "#1e293b",
          subtle: "#334155",
          accent: "#38bdf8",
          normal: "#10b981",
          attack: "#ef4444",
          warning: "#f59e0b",
          critical: "#dc2626"
        }
      }
    },
  },
  plugins: [],
}
