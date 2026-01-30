let accessToken: string | null = null;

export const token = {
  getAccessToken(): string | null {
    return accessToken;
  },
  setAccessToken(token: string | null) {
    accessToken = token;
  },
};
