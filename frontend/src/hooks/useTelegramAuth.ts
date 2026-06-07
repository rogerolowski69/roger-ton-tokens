import { useCallback, useEffect, useState } from 'react';
import { apiFetch, AuthMe, getInitData } from '../lib/api';

export function useTelegramAuth() {
  const [user, setUser] = useState<AuthMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inTelegram, setInTelegram] = useState(false);

  const refresh = useCallback(async () => {
    const init = getInitData();
    setInTelegram(Boolean(init));

    if (!init) {
      setUser(null);
      setError('Open inside Telegram for authenticated checkout.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const me = await apiFetch<AuthMe>('/api/auth/me');
      setUser(me);
    } catch (e) {
      setUser(null);
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
    void refresh();
  }, [refresh]);

  return { user, loading, error, inTelegram, refresh };
}
