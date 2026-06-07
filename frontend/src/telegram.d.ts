declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready: () => void;
        expand: () => void;
        enableClosingConfirmation: () => void;
        openLink: (url: string) => void;
        initData: string;
        initDataUnsafe?: { user?: { id?: number; username?: string; first_name?: string } };
        themeParams: Record<string, string>;
        colorScheme: 'light' | 'dark';
        openInvoice: (
          url: string,
          callback?: (
            status: 'paid' | 'cancelled' | 'failed' | 'pending',
          ) => void,
        ) => void;
        HapticFeedback?: { notificationOccurred: (type: string) => void };
      };
    };
  }
}

export {};
