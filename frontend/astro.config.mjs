import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwind from "@astrojs/tailwind";

const root = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  integrations: [react(), tailwind({ applyBaseStyles: false })],
  output: "static",
  server: { port: 5173, host: true },
  vite: {
    resolve: {
      alias: { "@": path.resolve(root, "./src") },
    },
  },
});
