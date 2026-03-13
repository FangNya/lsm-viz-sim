import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const httpTarget = process.env.VITE_BACKEND_HTTP_TARGET ?? "http://127.0.0.1:8000";
const wsTarget = process.env.VITE_BACKEND_WS_TARGET ?? "ws://127.0.0.1:8000";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/sim": {
        target: httpTarget,
        changeOrigin: true
      },
      "/ws": {
        target: wsTarget,
        ws: true
      }
    }
  }
});
