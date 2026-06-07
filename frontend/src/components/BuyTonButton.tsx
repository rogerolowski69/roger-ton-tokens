import { useCallback, useState } from 'react';
import { useTonConnectUI } from '@tonconnect/ui-react';
import { apiFetch, TonPrepareResponse } from '../lib/api';

type Props = {
  sku: 'credit_1_usd' | 'hour_voucher_1h';
  onSuccess?: () => void;
};

export function BuyTonButton({ sku, onSuccess }: Props) {
  const [tonConnectUI] = useTonConnectUI();
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');

  const payWithTon = useCallback(async () => {
    if (!tonConnectUI) {
      setStatus('TonConnect not ready');
      return;
    }

    setBusy(true);
    setStatus('Preparing TON payment…');

    try {
      const prep = await apiFetch<TonPrepareResponse>('/api/checkout/ton/prepare', {
        method: 'POST',
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

      setStatus('Confirming on server…');

      await apiFetch('/api/checkout/ton/confirm', {
        method: 'POST',
        body: JSON.stringify({
          order_id: prep.order_id,
          tx_hash: result.boc.slice(0, 64),
        }),
      });

      setStatus('TON payment confirmed ✅');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      onSuccess?.();
    } catch (e) {
      setStatus((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [sku, tonConnectUI, onSuccess]);

  return (
    <button type="button" className="btn ton" disabled={busy} onClick={payWithTon}>
      {busy ? 'Processing…' : 'Pay with TON 💎'}
      {status ? <span className="btn-status">{status}</span> : null}
    </button>
  );
}
