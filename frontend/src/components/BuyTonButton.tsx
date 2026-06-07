import { useCallback, useState } from "react";
import { useTonConnectUI } from "@tonconnect/ui-react";
import { Button } from "@/components/ui/button";
import { apiFetch, type ProductSku, type TonPrepareResponse } from "@/lib/api";
import { refreshCheckoutState, useAppStore } from "@/stores/app-store";

type Props = {
  sku: ProductSku;
};

export function BuyTonButton({ sku }: Props) {
  const [tonConnectUI] = useTonConnectUI();
  const [busy, setBusy] = useState(false);
  const setStatusMessage = useAppStore((s) => s.setStatusMessage);

  const payWithTon = useCallback(async () => {
    if (!tonConnectUI) {
      setStatusMessage("TonConnect not ready");
      return;
    }

    setBusy(true);
    setStatusMessage("Preparing TON payment…");

    try {
      const prep = await apiFetch<TonPrepareResponse>("/api/checkout/ton/prepare", {
        method: "POST",
        body: JSON.stringify({ sku }),
      });

      const result = await tonConnectUI.sendTransaction({
        validUntil: Math.floor(Date.now() / 1000) + 300,
        messages: [
          {
            address: prep.merchant_address,
            amount: prep.amount_nano,
            payload: prep.comment,
          },
        ],
      });

      setStatusMessage("Confirming on server…");

      await apiFetch("/api/checkout/ton/confirm", {
        method: "POST",
        body: JSON.stringify({
          order_id: prep.order_id,
          tx_hash: result.boc.slice(0, 64),
        }),
      });

      setStatusMessage("TON payment confirmed");
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred("success");
      await refreshCheckoutState();
    } catch (e) {
      setStatusMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [sku, tonConnectUI, setStatusMessage]);

  return (
    <Button size="full" variant="outline" disabled={busy} onClick={payWithTon}>
      {busy ? "Processing…" : "Pay with TON"}
    </Button>
  );
}
