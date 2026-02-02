type JwtPayload = {
  sub?: string;
  exp?: number;
  [key: string]: unknown;
};

function base64UrlDecode(input: string): string {
  // base64url -> base64
  let str = input.replace(/-/g, '+').replace(/_/g, '/');
  const pad = str.length % 4;
  if (pad) {
    str += '='.repeat(4 - pad);
  }

  // Browsers + jsdom provide atob; Node provides Buffer.
  if (typeof globalThis.atob === 'function') {
    return globalThis.atob(str);
  }

  return Buffer.from(str, 'base64').toString('binary');
}

export function parseJwtPayload(jwt: string): JwtPayload | null {
  try {
    const parts = jwt.split('.');
    if (parts.length !== 3) {
      return null;
    }
    const payload = base64UrlDecode(parts[1]);
    return JSON.parse(payload) as JwtPayload;
  } catch {
    return null;
  }
}
