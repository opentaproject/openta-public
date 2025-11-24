import { defineConfig, loadEnv, splitVendorChunkPlugin } from 'vite';
import react from '@vitejs/plugin-react';
import { dependencies } from './package.json';

function renderChunks(deps) {
   let chunks = {};
   Object.keys(deps).forEach((key) => {
     //if (['react'].includes(key)) return;
     if (key.startsWith('react')) return;
     chunks[key] = [key];
   });
   return chunks;
 }

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  const proxyTarget = `${env.BACKEND_SERVER}`
  console.log('proxy target', proxyTarget);

  return {
    //plugins: [react(), splitVendorChunkPlugin()],
    plugins: [react()],
    server: {
      host: 'http://v320c.localhost',
      sourcemap: false ,
      port: 3000,
      minify: false,
      manifest: false,
      assetsDir: 'dist',
      rollupOptions: {
        input: 'src/main.jsx',
        output: {
          entryFileNames: `[name].js`,
          chunkFileNames: `[name].js`,
          assetFileNames: `[name].[ext]`,
        }
       },

      proxy: {
        '^/(login|loggedin|course|courses|exercise|exercises|hijack|health|statistics)/.*': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          samesite:'None',
          ws: true
        }
      }
    },

    build: {
      assetsDir: 'dist',
      minify: true,
      sourcemap: true,
      manifest: false,
      //manualChunks: {
      //  lodash: ['lodash'],
      //  codemirror: ['codemirror'],
      //  },
      rollupOptions: {
        input: 'src/main.jsx',
        output: {
          // see https://github.com/rollup/rollup/issues/2616#issuecomment-1264173137
        entryFileNames: `[name].js`,
        chunkFileNames: `[name].js`,
        assetFileNames: `[name].[ext]`,
        manualChunks: {
            vendor: ['react','react-dom' ],
             ...renderChunks(dependencies)
            }
        //dir: 'dist',
          //file: 'dist/app.js',
          // TEMPORARY: only here for debugging
          //     manualChunks: {
          //       vendor: ['react'],
          //       ...renderChunks(dependencies)
          //     }
        }
      }
    }
  };
});
