const API_BASE = import.meta.env.PUBLIC_API_BASE_URL ?? "";

export function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? "";
}

export function authHeaders(): HeadersInit {
  const init = getInitData();
  return init
    ? { "X-Telegram-Init-Data": init, Authorization: `tma ${init}` }
    : {};
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }

  return res.json() as Promise<T>;
}

export interface AuthMe {
  telegram_user_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  language_code: string | null;
  is_premium: boolean;
  photo_url: string | null;
}

export interface WalletStatus {
  connected: boolean;
  ton_address: string | null;
  wallet_app: string | null;
}

export interface BalanceResponse {
  telegram_user_id: number;
  balance_cents: number;
  balance_usd: string;
}

export interface TonPrepareResponse {
  order_id: string;
  merchant_address: string;
  amount_nano: string;
  comment: string;
}

export type ProductSku = "credit_1_usd" | "hour_voucher_1h";

export interface Product {
  sku: ProductSku;
  icon: string;
  name: string;
  description: string;
  price: string;
  stars: string;
  ton: string;
}

export const PRODUCTS: Product[] = [
  {
    sku: "credit_1_usd",
    icon: "💰",
    name: "$1 Website Credit",
    description: "Ledger-backed balance for tokens & services",
    price: "$1.00",
    stars: "50 Stars",
    ton: "~0.35 TON",
  },
  {
    sku: "hour_voucher_1h",
    icon: "🎟",
    name: "1 Hour Time Voucher",
    description: "Redeemable for 1 hr consulting — minted as TON voucher",
    price: "$1.00",
    stars: "50 Stars",
    ton: "~0.35 TON",
  },
];
