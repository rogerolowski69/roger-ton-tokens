import { useCallback, useEffect } from "react";
import { TonConnectButton, useTonAddress, useTonConnectUI } from "@tonconnect/ui-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, type WalletStatus } from "@/lib/api";
import { useAppStore } from "@/stores/app-store";

export function TonWalletSection() {
  const address = useTonAddress();
  const [tonConnectUI] = useTonConnectUI();
  const wallet = useAppStore((s) => s.wallet);
  const setWallet = useAppStore((s) => s.setWallet);
  const setStatusMessage = useAppStore((s) => s.setStatusMessage);

  const syncWallet = useCallback(
    async (addr: string) => {
      try {
        const walletApp = tonConnectUI?.wallet?.device?.appName ?? null;
        const res = await apiFetch<WalletStatus>("/api/wallet/connect", {
          method: "POST",
          body: JSON.stringify({ ton_address: addr, wallet_app: walletApp }),
        });
        setWallet(res);
        setStatusMessage("Wallet linked to your account");
      } catch (e) {
        setStatusMessage((e as Error).message);
      }
    },
    [setWallet, setStatusMessage, tonConnectUI?.wallet?.device?.appName],
  );

  useEffect(() => {
    if (address) {
      void syncWallet(address);
    }
  }, [address, syncWallet]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">TON Wallet</CardTitle>
        <TonConnectButton />
      </CardHeader>
      <CardContent>
        {wallet?.connected && wallet.ton_address ? (
          <p className="font-mono text-sm text-muted-foreground">
            {wallet.ton_address.slice(0, 6)}…{wallet.ton_address.slice(-4)}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">Connect to pay with TON</p>
        )}
      </CardContent>
    </Card>
  );
}
