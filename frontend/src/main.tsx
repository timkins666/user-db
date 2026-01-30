import { StrictMode, useState } from 'react';
import { createRoot } from 'react-dom/client';
import App from './UserManagement.tsx';
import Login from './Login';

function Root() {
  const [authenticated, setAuthenticated] = useState(
    () => localStorage.getItem('auth') === 'true'
  );

  return authenticated ? (
    <App />
  ) : (
    <Login onLogin={() => setAuthenticated(true)} />
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>
);
