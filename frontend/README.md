# DS Airlines interface

The React 19 and TypeScript front end for DS Airlines, built with Vite and
Tailwind v4 on the Airy Sky Editorial token layer in `src/design-system/`.

```
npm ci
npm run dev        # http://localhost:5173, talks to the API on :8000
npm run lint
npm run build      # tsc -b, then vite build
npm run test       # Vitest component tests
npm run test:e2e   # Playwright, needs the API running (see make e2e)
```

The API address comes from `VITE_API_URL` and defaults to
`http://localhost:8000/api`. From the repository root, `make dev` starts the
API and this interface together.

See the [root README](../README.md) and [docs/](../docs/README.md) for the
rest of the project.
