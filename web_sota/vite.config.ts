import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 11971,
    host: "127.0.0.1",
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:11970",
        changeOrigin: true,
      },
      "/mcp": {
        target: "http://127.0.0.1:11970",
        changeOrigin: true,
      },
    },
  },
});
