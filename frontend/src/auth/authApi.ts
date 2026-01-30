import axios from 'axios';
import { registerAccessTokenListener, token } from './authToken';

const REFRESH_BUFFER_SECONDS = 60;
let refreshTimeoutId: number | null = null;

function base64UrlDecode(input: string): string {
  // base64url -> base64
  let str = input.replace(/-/g, '+').replace(/_/g, '/');
  const pad = str.length % 4;
  if (pad) {
    str += '='.repeat(4 - pad);
  }
  return atob(str);
}

function parseJwtPayload(jwt: string): any | null {
  try {
    const parts = jwt.split('.');
    if (parts.length !== 3) {
      return null;
    }
    const payload = base64UrlDecode(parts[1]);
    return JSON.parse(payload);
  } catch {
    return null;
  }
}

export function scheduleRefreshForToken(accessToken: string | null) {
  if (refreshTimeoutId !== null) {
    clearTimeout(refreshTimeoutId);
    refreshTimeoutId = null;
  }

  if (!accessToken) {
    return;
  }

  const payload = parseJwtPayload(accessToken);
  if (!payload?.exp) {
    return;
  }

  // exp is seconds since epoch (UTC)
  const expiresAtMs = payload.exp * 1000;
  const refreshAtMs = expiresAtMs - REFRESH_BUFFER_SECONDS * 1000;
  const delay = refreshAtMs - Date.now();

  if (delay <= 0) {
    void refreshAccessToken().catch(() => {
      // ignore; request layer can handle auth failures
    });
    return;
  }

  refreshTimeoutId = window.setTimeout(() => {
    console.info('proactively refreshing access token');
    void refreshAccessToken().catch(() => {
      // ignore; request layer can handle auth failures
    });
  }, delay);
}

// keep scheduling in sync with any token updates (login, refresh, logout)
registerAccessTokenListener((t) => {
  scheduleRefreshForToken(t);
});

export async function refreshAccessToken(): Promise<string> {
  const res = await axios.post(
    '/auth/refresh',
    {},
    {
      withCredentials: true,
    },
  );

  const newToken = res.data.access_token as string;
  token.setAccessToken(newToken);
  scheduleRefreshForToken(newToken);
  return newToken;
}
