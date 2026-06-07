import { useCallback, useEffect, useState } from 'react';
import { TonConnectButton, useTonAddress, useTonConnectUI } from '@tonconnect/ui-react';
import { apiFetch, WalletStatus } from '../lib/api';

type Props = {
  onConnected?: (address: string) => void;
};

export function TonWalletSection({ onConnected }: Props) {
  const address = useTonAddress();
  const [tonConnectUI] = useTonConnectUI();
  const [wallet, setWallet] = useState<WalletStatus | null>(null);
  const [status, setStatus] = useState('');

  const syncWallet = useCallback(async (addr: string) => {
    try {
      const walletApp = tonConnectUI?.wallet?.device?.appName ?? null;
      const res = await apiFetch<WalletStatus>('/api/wallet/connect', {
        method: 'POST',
        body: JSON.stringify({ ton_address: addr, wallet_app: walletApp }),
      });
      setWallet(res);
      setStatus('Wallet linked to your account');
      onConnected?.(addr);
    } catch (e) {
      setStatus((e as Error).message);
    }
  }, [onConnected, tonConnectUI?.wallet?.device?.appName]);

  useEffect(() => {
    void (async () => {
      try {
        const res = await apiFetch<WalletStatus>('/api/wallet');
        setWallet(res);
      } catch {
        /* not authed yet */
      }
    })();
  }, []);

  useEffect(() => {
    if (address) {
      void syncWallet(address);
    }
  }, [address, syncWallet]);

  return (
    <section className="wallet-card">
      <div className="wallet-header">
        <h3>TON Wallet</h3>
        <TonConnectButton />
      </div>
      {wallet?.connected && (
        <p className="wallet-addr">
          {wallet.ton_address?.slice(0, 6)}…{wallet.ton_address?.slice(-4)}
        </p>
      )}
      {status ? <p className="status">{status}</p> : null}
    </section>
  );
}
