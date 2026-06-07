import { useCallback, useState } from "react";
import { Button } from "@/components/ui/button";
import { apiFetch, type ProductSku } from "@/lib/api";
import { refreshCheckoutState, useAppStore } from "@/stores/app-store";

type Props = {
  sku: ProductSku;
  starsLabel: string;
};

export function BuyStarsButton({ sku, starsLabel }: Props) {
  const [busy, setBusy] = useState(false);
  const setStatusMessage = useAppStore((s) => s.setStatusMessage);

  const buyWithStars = useCallback(async () => {
    const tg = window.Telegram?.WebApp;
    if (!tg?.initData) {
      setStatusMessage("Open this inside Telegram.");
      return;
    }

    setBusy(true);
    setStatusMessage("Creating invoice…");

    try {
      const { invoice_link } = await apiFetch<{ invoice_link: string }>(
        "/api/checkout/stars/invoice-link",
        { method: "POST", body: JSON.stringify({ sku }) },
      );

      tg.openInvoice(invoice_link, (invoiceStatus) => {
        setBusy(false);
        if (invoiceStatus === "paid") {
          setStatusMessage("Payment sent — confirming on server…");
          tg.HapticFeedback?.notificationOccurred("success");
          void refreshCheckoutState();
        } else if (invoiceStatus === "cancelled") {
          setStatusMessage("Payment cancelled.");
        }
      });
    } catch (e) {
      setBusy(false);
      setStatusMessage((e as Error).message);
    }
  }, [sku, setStatusMessage]);

  const payWithStoreCredit = useCallback(async () => {
    setBusy(true);
    setStatusMessage("Spending store credit…");

    try {
      const data = await apiFetch<{ order_id: string }>("/api/checkout/store-credit/pay", {
        method: "POST",
        body: JSON.stringify({ sku }),
      });
      setStatusMessage(`Paid with credit — order ${data.order_id.slice(0, 8)}…`);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred("success");
      await refreshCheckoutState();
    } catch (e) {
      setStatusMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [sku, setStatusMessage]);

  return (
    <div className="flex flex-col gap-2">
      <Button size="full" disabled={busy} onClick={buyWithStars}>
        Stars — {starsLabel}
      </Button>
      <Button size="full" variant="secondary" disabled={busy} onClick={payWithStoreCredit}>
        Pay with Store Credit
      </Button>
    </div>
  );
}
