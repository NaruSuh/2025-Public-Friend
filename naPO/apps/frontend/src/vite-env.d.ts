/// <reference types="vite/client" />

// CSS Modules
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}

// Vite Environment Variables
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_ENABLE_NL_QUERY: string;
  readonly VITE_ENABLE_OCR: string;
  readonly MODE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
