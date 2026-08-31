import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        aqi: {
          good: "#00b25d",
          satisfactory: "#92d050",
          moderate: "#ffd21e",
          poor: "#f78104",
          verypoor: "#e2231a",
          severe: "#7d2181",
        },
        brand: {
          50: "#ecfdf5",
          200: "#a7f3d0",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
      },
      boxShadow: {
        card: "0 1px 0 0 rgba(255,255,255,0.03) inset, 0 10px 30px -12px rgba(0,0,0,0.6)",
        "card-hover":
          "0 1px 0 0 rgba(255,255,255,0.05) inset, 0 18px 44px -14px rgba(0,0,0,0.75), 0 0 0 1px rgba(52,211,153,0.12)",
        glow: "0 0 24px -6px rgba(52,211,153,0.45)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-emerald":
          "linear-gradient(120deg, rgba(16,185,129,0.12), rgba(56,189,248,0.10))",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "shimmer": "shimmer 1.8s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
