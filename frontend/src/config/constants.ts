// Prefer Vite's `import.meta.env` when available so Vite can statically replace
// `import.meta.env` with the environment object at build/dev time. Fall back
// to `process.env` for Node/Jest environments where `import.meta.env` isn't
// available.
let _env: any = {};

if (typeof import.meta !== 'undefined' && (import.meta as any).env) {
  // Keep the direct `import.meta.env` access so Vite's static replacement works.
  _env = (import.meta as any).env;
} else {
  _env = typeof process !== 'undefined' ? (process.env as any) : {};
}

export const API_URL = _env.VITE_BACKEND_FASTAPI_URL;

export const MIN_USER_AGE = 16;
