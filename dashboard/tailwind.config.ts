import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "never", // Disable dark mode
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
};

export default config;
