import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './styles.css'
import { LangProvider } from './i18n'
import Hall from './pages/Hall'
import Room from './pages/Room'
import Desk from './pages/Desk'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <LangProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Hall />} />
          <Route path="/room/:code" element={<Room />} />
          <Route path="/desk/:code" element={<Desk />} />
        </Routes>
      </BrowserRouter>
    </LangProvider>
  </React.StrictMode>,
)
