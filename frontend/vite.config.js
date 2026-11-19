import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, strictPort: true }, // strictPort: bận thì báo lỗi, không tự nhảy port (CORS backend chỉ cho port đã khai báo)
});
