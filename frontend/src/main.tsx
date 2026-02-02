import { StrictMode, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import UserManagement from "./pages/UserManagement";
import Login from "./pages/Login";
import { refreshAccessToken } from "./auth/authApi";
import TopBannerStripe from "./components/TopBannerStripe";

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
    <TopBannerStripe>
      <UserManagement />
    </TopBannerStripe>
  ) : (
    <Login onLogin={() => setAuthenticated(true)} />
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
