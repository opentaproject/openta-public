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
        '^(?!/$|/(app|src|js|css|fonts|node_modules|@|katex)).*$': {
          target: proxyTarget,
          changeOrigin: true,
          secure: true,
          samesite:'None',
          ws: true
        }
      }
    },
    // jsoneditor breaks collectstatic 
    // in django environement
    // touch env/lib/python3.10/site-packages/django_json_widget/static/dist/jsoneditor.map 
    // also cp extra/app.css.map to dist
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
            vendor: ['react','react-dom' ], //,'plotly.js-dist-min' ],
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
