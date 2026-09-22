import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './styles.css'
import { requireBranchAuth } from './auth'

const session = requireBranchAuth()

session && createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
