let accessToken: string | null = null;
const listeners: Array<(token: string | null) => void> = [];

export const token = {
  getAccessToken(): string | null {
    return accessToken;
  },
  setAccessToken(tokenValue: string | null) {
    accessToken = tokenValue;
    // notify listeners (best-effort)
    for (const l of listeners) {
      try {
        l(accessToken);
      } catch (e) {
        // ignore listener errors
      }
    }
  },
};

export function registerAccessTokenListener(
  listener: (token: string | null) => void,
) {
  listeners.push(listener);
}
