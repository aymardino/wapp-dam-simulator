import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './styles.css'
import { LangProvider } from './i18n'
import Hall from './pages/Hall'
import Room from './pages/Room'
import Desk from './pages/Desk'
import Guide from './pages/Guide'
import Landing from './pages/Landing'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LangProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/app" element={<Hall />} />
          <Route path="/room/:code" element={<Room />} />
          <Route path="/desk/:code" element={<Desk />} />
          <Route path="/guide/:who" element={<Guide />} />
        </Routes>
      </BrowserRouter>
    </LangProvider>
  </React.StrictMode>,
)
