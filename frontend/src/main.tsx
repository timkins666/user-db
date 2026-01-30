import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import App from './UserManagement.tsx';
import Login from './Login';
import { refreshAccessToken } from './auth/authApi';

function Root() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  const bootstrappedRef = useRef(false);

  useEffect(() => {
    // React 18 StrictMode runs effects twice in dev; avoid double refresh calls.
    if (bootstrappedRef.current) return;
    bootstrappedRef.current = true;

    (async () => {
      try {
        await refreshAccessToken();
        setAuthenticated(true);
      } catch {
        setAuthenticated(false);
      }
    })();
  }, []);

  if (authenticated === null) {
    // minimal loading state
    return null;
  }

  return authenticated ? (
    <App />
  ) : (
    <Login onLogin={() => setAuthenticated(true)} />
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
