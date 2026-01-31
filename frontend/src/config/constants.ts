let _env: any = {};
try {
  // Attempt to read `import.meta.env` in environments where it's available (Vite).
  // Use the Function constructor so the token `import.meta` doesn't appear directly
  // in the module source, avoiding syntax errors in Node/Jest.
  // If this fails (e.g., tests running in Node), fall back to `process.env`.
  // eslint-disable-next-line no-new-func
  _env = Function('return import.meta.env')();
} catch {
  _env = typeof process !== 'undefined' ? (process.env as any) : {};
}

export const API_URL = _env.VITE_BACKEND_FASTAPI_URL;

export const MIN_USER_AGE = 16;
