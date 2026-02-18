import { BrowserRouter, Routes, Route, useLocation, Navigate, Outlet } from "react-router-dom"

import PageShell from "./components/layout/PageShell.jsx"
import TopNav from "./components/layout/TopNav.jsx"
import Footer from "./components/layout/Footer.jsx"

import MapPage from "./pages/MapPage.jsx"
import TelemetryPage from "./pages/TelemetryPage.jsx"
import LoginPage from "./pages/LoginPage.jsx"
import HomePage from "./pages/HomePage.jsx"
import DocsPage from "./pages/DocsPage.jsx"
import FlotaPage from "./pages/FlotaPage.jsx"
import CostsModelPage from "./pages/CostsModelPage.jsx";

import { AuthProvider } from "./auth/AuthContext.jsx"
import ProtectedRoute from "./auth/ProtectedRoute.jsx"


// Mapea ruta -> clave activa para TopNav
function useActiveKey() {
  const { pathname } = useLocation();

  if (pathname.startsWith("/flota")) return "flota"
  if (pathname.startsWith("/telemetry")) return "telemetry";
  if (pathname.startsWith("/mapa")) return "map";
  if (pathname.startsWith("/docs")) return "docs";
  if (pathname.startsWith("/costos")) return "costos";
  if (pathname === "/home" || pathname === "/") return "home";

  return null;
}

// Layout con TopNav + contenido (para rutas protegidas)
function AppFrame() {
  const activeKey = useActiveKey();

  const tabs = [
    { key: "home", label: "Home" },
    { key: "docs", label: "Documentación" },
    { key: "map", label: "Mapa (Rutas)" },
    { key: "flota", label: "Flotilla" },
    { key: "telemetry", label: "Telemetría" },
    { key: "costos", label: "Modelo costos" },
  ];

  return (
    <PageShell>
      {/* Fila 1 del grid: barra superior */}
      <TopNav brand={null} tabs={tabs} activeKey={activeKey} />

      {/* Fila 2 del grid: TODO el contenido + footer */}
      <main className="app-main">
        <Outlet />
        <Footer />
      </main>
    </PageShell>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Login público */}
          <Route path="/login" element={<LoginPage />} />

          {/* Todo lo demás protegido por login */}
          <Route
            element={
              <ProtectedRoute>
                <AppFrame />
              </ProtectedRoute>
            }
          >
            <Route path="/home" element={<HomePage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/mapa" element={<MapPage />} />
            <Route path="/flota" element={<FlotaPage />} />
            <Route path="/telemetry" element={<TelemetryPage />} />
            <Route path="/costos" element={<CostsModelPage />} />

            {/* Redirecciones cómodas */}
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}