import { BrowserRouter, Route, Routes } from 'react-router'
import { Layout } from './components/Layout'
import { CamerasPage } from './pages/CamerasPage'
import { DashboardPage } from './pages/DashboardPage'
import { IncidentsPage } from './pages/IncidentsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { StatusPage } from './pages/StatusPage'
import { VideoTestingPage } from './pages/VideoTestingPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="cameras" element={<CamerasPage />} />
          <Route path="video-testing" element={<VideoTestingPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="status" element={<StatusPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
