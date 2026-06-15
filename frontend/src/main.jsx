import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import Shell from './components/Shell'
import LiveCall from './pages/LiveCall'
import Calls from './pages/Calls'
import CallDetail from './pages/CallDetail'
import Knowledge from './pages/Knowledge'
import Experiments from './pages/Experiments'
import Personas from './pages/Personas'
import Overview from './pages/Overview'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<LiveCall />} />
          <Route path="/calls" element={<Calls />} />
          <Route path="/calls/:id" element={<CallDetail />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/personas" element={<Personas />} />
          <Route path="/overview" element={<Overview />} />
        </Routes>
      </Shell>
    </HashRouter>
  </React.StrictMode>
)
