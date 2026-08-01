import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './design-system/tokens/index.css'
import './design-system/overrides.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
