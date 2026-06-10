/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#121826",
        muted: "#667085",
        line: "#d7dee8",
        brand: "#1f56d8",
        bridge: "#009285",
        warning: "#eb7f08",
        danger: "#d63838",
        success: "#0f8f46",
      },
      boxShadow: {
        panel: "0 16px 38px rgba(18, 24, 38, 0.08)",
      },
    },
  },
  plugins: [],
};
