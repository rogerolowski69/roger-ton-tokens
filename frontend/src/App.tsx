import { TonConnectUIProvider } from '@tonconnect/ui-react';
import { BuyStarsButton, useCreditBalance } from './components/BuyStarsButton';
import { BuyTonButton } from './components/BuyTonButton';
import { TonWalletSection } from './components/TonWalletSection';
import { useTelegramAuth } from './hooks/useTelegramAuth';
import './app.css';

const MANIFEST = `${window.location.origin}/tonconnect-manifest.json`;

const PRODUCTS = [
  {
    sku: 'credit_1_usd' as const,
    icon: '💰',
    name: '$1 Website Credit',
    description: 'Ledger-backed balance for tokens & services',
    price: '$1.00',
    stars: '50 Stars',
    ton: '~0.35 TON',
  },
  {
    sku: 'hour_voucher_1h' as const,
    icon: '🎟',
    name: '1 Hour Time Voucher',
    description: 'Redeemable for 1 hr consulting — minted as TON voucher',
    price: '$1.00',
    stars: '50 Stars',
    ton: '~0.35 TON',
  },
];

function Storefront() {
  const { user, loading, error, inTelegram } = useTelegramAuth();
  const { usd, refresh } = useCreditBalance();

  const displayName = user?.username
    ? `@${user.username}`
    : user?.first_name
      ? user.first_name
      : inTelegram
        ? '…'
        : '@guest';

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="logo">ROGER<span>TON</span></div>
          <div className="tagline">tokens & consulting</div>
        </div>
        <div className="user-badge">{loading ? '…' : displayName}</div>
      </header>

      {error && !user ? <div className="auth-banner">{error}</div> : null}

      <section className="balance-strip">
        <div>
          <div className="strip-label">Store credit</div>
          <div className="strip-value">{usd}</div>
        </div>
      </section>

      <main className="main">
        <TonWalletSection />

        <h1 className="section-title">Store</h1>
        <p className="section-sub">
          Pay with Stars, store credit, or TON wallet via TonConnect
        </p>

        <div className="product-grid">
          {PRODUCTS.map((p) => (
            <article key={p.sku} className="product-card">
              <div className="product-icon">{p.icon}</div>
              <h2 className="product-name">{p.name}</h2>
              <p className="product-desc">{p.description}</p>
              <div className="product-meta">
                <span className="price">{p.price}</span>
                <span className="stars">{p.stars}</span>
                <span className="ton-tag">{p.ton}</span>
              </div>
              <BuyStarsButton sku={p.sku} label={`Stars — ${p.stars}`} onSuccess={refresh} />
              <BuyTonButton sku={p.sku} onSuccess={refresh} />
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}

export function App() {
  return (
    <TonConnectUIProvider manifestUrl={MANIFEST}>
      <Storefront />
    </TonConnectUIProvider>
  );
}
