"use client"
import { NavLink, useNavigate } from "react-router-dom"
import EAFITLogo from "../../images/EAFIT.jpg"  // asegúrate del nombre/ruta

export default function TopNav({ brand, tabs = [], activeKey }) {
  const navigate = useNavigate()

  const routeByKey = {
    home: "/home",
    docs: "/docs",
    map: "/mapa",
    telemetry: "/telemetry",
  }

  return (
    <header className="topnav-black">
      {/* Logo izquierda: SOLO imagen */}
      <button
        className="user-icon"
        onClick={() => navigate("/home")}
        title="EAFIT"
      >
        <img
          src={EAFITLogo}
          alt="EAFIT Logo"
          className="user-logo-img"
        />
      </button>

      {/* Navegación centrada */}
      <nav className="topnav-nav">
        {tabs.map((tab) => {
          const path = routeByKey[tab.key] || "/home"
          return (
            <NavLink
              key={tab.key}
              to={path}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              {tab.label}
            </NavLink>
          )
        })}
      </nav>

    </header>
  )
}
