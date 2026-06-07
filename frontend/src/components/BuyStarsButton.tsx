import { useCallback, useEffect, useState } from 'react';
import { apiFetch, BalanceResponse } from '../lib/api';

type Props = {
  sku: 'credit_1_usd' | 'hour_voucher_1h';
  label?: string;
  onSuccess?: () => void;
};

export function BuyStarsButton({ sku, label, onSuccess }: Props) {
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  const buyWithStars = useCallback(async () => {
    const tg = window.Telegram?.WebApp;
    if (!tg?.initData) {
      setStatus('Open this inside Telegram.');
      return;
    }

    setBusy(true);
    setStatus('Creating invoice…');

    try {
      const { invoice_link } = await apiFetch<{ invoice_link: string }>(
        '/api/checkout/stars/invoice-link',
        { method: 'POST', body: JSON.stringify({ sku }) },
      );

      tg.openInvoice(invoice_link, (invoiceStatus) => {
        setBusy(false);
        if (invoiceStatus === 'paid') {
          setStatus('Payment sent — confirming on server…');
          tg.HapticFeedback?.notificationOccurred('success');
          onSuccess?.();
        } else if (invoiceStatus === 'cancelled') {
          setStatus('Payment cancelled.');
        }
      });
    } catch (e) {
      setBusy(false);
      setStatus((e as Error).message);
    }
  }, [sku, onSuccess]);

  const payWithStoreCredit = useCallback(async () => {
    setBusy(true);
    setStatus('Spending store credit…');

    try {
      const data = await apiFetch<{ order_id: string }>('/api/checkout/store-credit/pay', {
        method: 'POST',
        body: JSON.stringify({ sku }),
      });
      setStatus(`Paid with credit — order ${data.order_id.slice(0, 8)}…`);
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      onSuccess?.();
    } catch (e) {
      setStatus((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [sku, onSuccess]);

  return (
    <div className="buy-stars-group">
      <button type="button" className="btn primary" disabled={busy} onClick={buyWithStars}>
        {label ?? 'Buy with Stars ⭐'}
      </button>
      <button type="button" className="btn secondary" disabled={busy} onClick={payWithStoreCredit}>
        Pay with Store Credit 🧾
      </button>
      {status ? <p className="status">{status}</p> : null}
    </div>
  );
}

export function useCreditBalance(): { cents: number; usd: string; refresh: () => void } {
  const [cents, setCents] = useState(0);

  const refresh = useCallback(async () => {
    if (!window.Telegram?.WebApp?.initData) return;
    try {
      const data = await apiFetch<BalanceResponse>('/api/checkout/balance');
      setCents(data.balance_cents ?? 0);
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { cents, usd: `$${(cents / 100).toFixed(2)}`, refresh };
}
