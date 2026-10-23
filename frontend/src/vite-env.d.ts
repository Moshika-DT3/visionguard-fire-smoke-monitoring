/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional absolute backend URL, e.g. http://127.0.0.1:8000. Leave unset to use the dev proxy. */
  readonly VITE_API_BASE_URL?: string
  /** Backend URL the dev/preview proxy forwards /api to. Defaults to http://127.0.0.1:8000. */
  readonly VITE_BACKEND_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
