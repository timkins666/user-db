import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default ({ mode }: { mode: string }) => {
  // load env into `process.env` as well as return an object
  const env = loadEnv(mode, process.cwd());

  const backendProxy = env.VITE_BACKEND_FASTAPI_PROXY;

  const serverConfig: any = {};

  if (backendProxy) {
    serverConfig.proxy = {
      '/auth': {
        target: backendProxy,
        changeOrigin: true,
      },
    };
    serverConfig.watch = { usePolling: true };
  }

  return defineConfig({
    plugins: [react()],
    server: serverConfig,
  });
};
