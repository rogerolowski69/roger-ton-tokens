import { create } from "zustand";
import {
  apiFetch,
  type AuthMe,
  type BalanceResponse,
  type WalletStatus,
} from "@/lib/api";

interface AppState {
  user: AuthMe | null;
  authLoading: boolean;
  authError: string | null;
  inTelegram: boolean;
  balanceCents: number;
  wallet: WalletStatus | null;
  statusMessage: string | null;
  setStatusMessage: (message: string | null) => void;
  refreshAuth: () => Promise<void>;
  refreshBalance: () => Promise<void>;
  refreshWallet: () => Promise<void>;
  setWallet: (wallet: WalletStatus | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  authLoading: true,
  authError: null,
  inTelegram: false,
  balanceCents: 0,
  wallet: null,
  statusMessage: null,

  setStatusMessage: (message) => set({ statusMessage: message }),

  refreshAuth: async () => {
    const init = window.Telegram?.WebApp?.initData ?? "";
    set({ inTelegram: Boolean(init) });

    if (!init) {
      set({
        user: null,
        authError: "Open inside Telegram for authenticated checkout.",
        authLoading: false,
      });
      return;
    }

    set({ authLoading: true, authError: null });
    try {
      const user = await apiFetch<AuthMe>("/api/auth/me");
      set({ user, authLoading: false });
    } catch (e) {
      set({
        user: null,
        authError: (e as Error).message,
        authLoading: false,
      });
    }
  },

  refreshBalance: async () => {
    if (!window.Telegram?.WebApp?.initData) return;
    try {
      const data = await apiFetch<BalanceResponse>("/api/checkout/balance");
      set({ balanceCents: data.balance_cents ?? 0 });
    } catch {
      /* silent */
    }
  },

  refreshWallet: async () => {
    if (!window.Telegram?.WebApp?.initData) return;
    try {
      const wallet = await apiFetch<WalletStatus>("/api/wallet");
      set({ wallet });
    } catch {
      set({ wallet: null });
    }
  },

  setWallet: (wallet) => set({ wallet }),
}));

export function useBalanceUsd(): string {
  const cents = useAppStore((s) => s.balanceCents);
  return `$${(cents / 100).toFixed(2)}`;
}

export async function refreshCheckoutState(): Promise<void> {
  const { refreshBalance, refreshWallet } = useAppStore.getState();
  await Promise.all([refreshBalance(), refreshWallet()]);
}
