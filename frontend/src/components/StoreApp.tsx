import { useEffect } from "react";
import { TonConnectUIProvider } from "@tonconnect/ui-react";
import WebApp from "@twa-dev/sdk";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ProductCard } from "@/components/ProductCard";
import { StatusDialog } from "@/components/StatusDialog";
import { TonWalletSection } from "@/components/TonWalletSection";
import { PRODUCTS } from "@/lib/api";
import { useAppStore, useBalanceUsd } from "@/stores/app-store";

const MANIFEST = `${window.location.origin}/tonconnect-manifest.json`;

function Storefront() {
  const user = useAppStore((s) => s.user);
  const authLoading = useAppStore((s) => s.authLoading);
  const authError = useAppStore((s) => s.authError);
  const inTelegram = useAppStore((s) => s.inTelegram);
  const statusMessage = useAppStore((s) => s.statusMessage);
  const setStatusMessage = useAppStore((s) => s.setStatusMessage);
  const refreshAuth = useAppStore((s) => s.refreshAuth);
  const refreshBalance = useAppStore((s) => s.refreshBalance);
  const refreshWallet = useAppStore((s) => s.refreshWallet);
  const balanceUsd = useBalanceUsd();

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    WebApp.enableClosingConfirmation();
    void refreshAuth();
    void refreshBalance();
    void refreshWallet();
  }, [refreshAuth, refreshBalance, refreshWallet]);

  const displayName = user?.username
    ? `@${user.username}`
    : user?.first_name
      ? user.first_name
      : inTelegram
        ? "…"
        : "@guest";

  return (
    <div className="mx-auto min-h-screen max-w-lg px-4 pb-8 pt-4">
      <header className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            ROGER<span className="text-primary">TON</span>
          </h1>
          <p className="text-sm text-muted-foreground">tokens & consulting</p>
        </div>
        <Badge variant="secondary">{authLoading ? "…" : displayName}</Badge>
      </header>

      {authError && !user ? (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{authError}</AlertDescription>
        </Alert>
      ) : null}

      <Card className="mb-4 bg-primary/10 border-primary/20">
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Store credit</p>
            <p className="text-2xl font-semibold">{balanceUsd}</p>
          </div>
        </CardContent>
      </Card>

      <div className="mb-6">
        <TonWalletSection />
      </div>

      <section>
        <h2 className="mb-1 text-lg font-semibold">Store</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Pay with Stars, store credit, or TON wallet via TonConnect
        </p>
        <div className="grid gap-4">
          {PRODUCTS.map((product) => (
            <ProductCard key={product.sku} product={product} />
          ))}
        </div>
      </section>

      <StatusDialog
        open={Boolean(statusMessage)}
        title="Payment status"
        message={statusMessage ?? ""}
        onClose={() => setStatusMessage(null)}
      />
    </div>
  );
}

export function StoreApp() {
  return (
    <TonConnectUIProvider manifestUrl={MANIFEST}>
      <Storefront />
    </TonConnectUIProvider>
  );
}
