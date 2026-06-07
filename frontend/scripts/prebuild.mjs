import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const publicDir = path.join(root, "public");

const baseUrl =
  process.env.VITE_MINI_APP_URL?.replace(/\/$/, "") ||
  (process.env.RAILWAY_PUBLIC_DOMAIN
    ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
    : "http://localhost:5173");

const manifest = {
  url: baseUrl,
  name: "Roger TON Tokens",
  iconUrl: `${baseUrl}/icon.svg`,
  termsOfUseUrl: `${baseUrl}/terms`,
  privacyPolicyUrl: `${baseUrl}/privacy`,
};

fs.writeFileSync(
  path.join(publicDir, "tonconnect-manifest.json"),
  `${JSON.stringify(manifest, null, 2)}\n`,
);

console.log(`Wrote tonconnect-manifest.json for ${baseUrl}`);
