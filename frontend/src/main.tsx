import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { GoogleOAuthProvider } from '@react-oauth/google';
import App from './App.tsx';
import { GoogleClientIdContext } from './GoogleClientContext.tsx';
import './index.css';

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

function Root() {
  const [googleClientId, setGoogleClientId] = useState<string | null | undefined>(undefined);

  useEffect(() => {
    fetch(`${API_BASE}/auth/public-google-client-id`)
      .then((r) => r.json())
      .then((d: { client_id: string | null }) => {
        const id = d.client_id?.trim();
        setGoogleClientId(id || null);
      })
      .catch(() => setGoogleClientId(null));
  }, []);

  if (googleClientId === undefined) {
    return (
      <div className="min-h-screen grid place-items-center bg-background text-foreground font-sans">
        <p className="text-sm text-muted-foreground">Cargando…</p>
      </div>
    );
  }

  const tree = (
    <GoogleClientIdContext.Provider value={googleClientId}>
      <App />
    </GoogleClientIdContext.Provider>
  );

  return googleClientId ? <GoogleOAuthProvider clientId={googleClientId}>{tree}</GoogleOAuthProvider> : tree;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
