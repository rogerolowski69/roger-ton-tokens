const API_BASE = import.meta.env.VITE_API_BASE_URL;

export function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? '';
}

export function authHeaders(): HeadersInit {
  const init = getInitData();
  return init
    ? { 'X-Telegram-Init-Data': init, Authorization: `tma ${init}` }
    : {};
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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
