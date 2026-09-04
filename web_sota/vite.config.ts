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
  define: {
    "import.meta.env.VITE_API_BASE": JSON.stringify("http://127.0.0.1:11970"),
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          vendor: ["zustand", "lucide-react", "three"],
        },
      },
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
