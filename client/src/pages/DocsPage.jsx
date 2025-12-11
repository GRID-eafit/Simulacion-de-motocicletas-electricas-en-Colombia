"use client"

import { useState } from "react"
import TopNav from "../components/layout/TopNav"
import Footer from "../components/layout/Footer"

export default function DocsPage() {
  const [activeSection, setActiveSection] = useState("introduccion")

  const sections = [
    { id: "introduccion", label: "Introducción" },
    { id: "estructura", label: "Estructura del Proyecto" },
    { id: "api", label: "API Endpoints" },
    { id: "json", label: "Formato JSON" },
    { id: "autenticacion", label: "Autenticación" },
    { id: "ejemplos", label: "Ejemplos de Uso" },
  ]

  const styles = `
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
      background: #f5f5f5;
      color: #2c3e50;
    }

    .docs-wrapper {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }

    /* Updated layout to match Figma with header and footer */
    .docs-container {
      flex: 1;
      display: flex;
      gap: 2rem;
      padding: 2rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    .docs-sidebar {
      width: 280px;
      background: white;
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      height: fit-content;
      position: sticky;
      top: 2rem;
    }

    .docs-sidebar h3 {
      font-size: 0.875rem;
      font-weight: 600;
      color: #1a1a1a;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 1rem;
    }

    .docs-nav {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .docs-nav-item {
      padding: 0.75rem 1rem;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.95rem;
      color: #666;
      border-left: 3px solid transparent;
    }

    .docs-nav-item:hover {
      background: #f5f5f5;
      color: #1a1a1a;
    }

    .docs-nav-item.active {
      background: #f0f0f0;
      color: #000;
      border-left-color: #000;
      font-weight: 600;
    }

    .docs-content {
      flex: 1;
      background: white;
      border-radius: 12px;
      padding: 3rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    .docs-content h1 {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      color: #1a1a1a;
      font-weight: 700;
    }

    .docs-content h2 {
      font-size: 1.75rem;
      margin-top: 2rem;
      margin-bottom: 1rem;
      color: #1a1a1a;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid #f0f0f0;
      font-weight: 700;
    }

    .docs-content h3 {
      font-size: 1.25rem;
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      color: #333;
      font-weight: 600;
    }

    .docs-content p {
      line-height: 1.8;
      margin-bottom: 1rem;
      color: #555;
      font-size: 1rem;
    }

    .docs-content ul,
    .docs-content ol {
      margin-left: 1.5rem;
      margin-bottom: 1rem;
      line-height: 1.8;
    }

    .docs-content li {
      margin-bottom: 0.5rem;
      color: #555;
    }

    .code-block {
      background: #1e1e1e;
      border-radius: 8px;
      padding: 1.5rem;
      margin: 1.5rem 0;
      overflow-x: auto;
      border: 1px solid #333;
    }

    .code-block code {
      color: #e2e8f0;
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
      line-height: 1.6;
    }

    .endpoint {
      background: #f9f9f9;
      border-left: 4px solid #1a1a1a;
      padding: 1.5rem;
      margin: 1.5rem 0;
      border-radius: 8px;
    }

    .endpoint-method {
      display: inline-block;
      padding: 0.25rem 0.75rem;
      border-radius: 4px;
      font-weight: 600;
      font-size: 0.85rem;
      margin-right: 0.5rem;
      margin-bottom: 0.5rem;
    }

    .method-get {
      background: #e8e8e8;
      color: #1a1a1a;
    }

    .method-post {
      background: #d0d0d0;
      color: #1a1a1a;
    }

    .method-put {
      background: #c0c0c0;
      color: #1a1a1a;
    }

    .method-delete {
      background: #a0a0a0;
      color: white;
    }

    .endpoint-url {
      font-family: 'Courier New', monospace;
      color: #1a1a1a;
      font-weight: 600;
    }

    .note {
      background: #f5f5f5;
      border-left: 4px solid #1a1a1a;
      padding: 1rem 1.5rem;
      margin: 1.5rem 0;
      border-radius: 8px;
    }

    .note strong {
      color: #1a1a1a;
    }

    .note p {
      color: #333;
      margin: 0;
    }

    .table-wrapper {
      overflow-x: auto;
      margin: 1.5rem 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
    }

    table th {
      background: #f0f0f0;
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      color: #1a1a1a;
      border-bottom: 2px solid #e0e0e0;
    }

    table td {
      padding: 0.875rem 1rem;
      border-bottom: 1px solid #e0e0e0;
      color: #555;
    }

    table tr:hover {
      background: #fafafa;
    }

    @media (max-width: 1024px) {
      .docs-container {
        flex-direction: column;
        gap: 1rem;
      }

      .docs-sidebar {
        width: 100%;
        position: static;
      }

      .docs-content {
        padding: 2rem;
      }

      .docs-content h1 {
        font-size: 2rem;
      }
    }

    @media (max-width: 640px) {
      .docs-container {
        padding: 1rem;
      }

      .docs-sidebar {
        padding: 1.5rem;
      }

      .docs-content {
        padding: 1.5rem;
      }

      .docs-content h1 {
        font-size: 1.5rem;
      }

      .docs-content h2 {
        font-size: 1.25rem;
      }
    }
  `

  return (
    <>
      <style>{styles}</style>
      <div className="docs-wrapper">
        <div className="docs-container">
          {/* Sidebar */}
          <aside className="docs-sidebar">
            <h3>Contenido</h3>
            <nav className="docs-nav">
              {sections.map((section) => (
                <div
                  key={section.id}
                  className={`docs-nav-item ${activeSection === section.id ? "active" : ""}`}
                  onClick={() => setActiveSection(section.id)}
                >
                  {section.label}
                </div>
              ))}
            </nav>
          </aside>

          {/* Main Content */}
          <main className="docs-content">
            {activeSection === "introduccion" && (
              <>
                <h1>Documentación - Simulador de motocicletas Eléctricas</h1>
                <p>
                  Bienvenido a la documentación completa del simulador de rutas para motocicletas eléctricas. Esta guía te
                  ayudará a entender la estructura del proyecto, los endpoints disponibles, y cómo integrar el API en tu
                  aplicación.
                </p>
                <p>
                  El simulador permite a los usuarios crear rutas, calcular consumo de energía, estimar tiempos de viaje
                  y analizar el desempeño de diferentes modelos de motocicletas eléctricas.
                </p>
              </>
            )}

            {activeSection === "estructura" && (
              <>
                <h2>Estructura del Proyecto</h2>
                <p>El proyecto está organizado de la siguiente manera:</p>
                <div className="code-block">
                  <code>{`project/
├── src/
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   └── DocsPage.jsx
│   ├── components/
│   │   └── [componentes reutilizables]
│   ├── auth/
│   │   └── AuthContext.jsx
│   └── App.jsx
├── public/
├── package.json
└── vite.config.js`}</code>
                </div>
                <h3>Directorios principales</h3>
                <ul>
                  <li>
                    <strong>pages/:</strong> Páginas principales de la aplicación
                  </li>
                  <li>
                    <strong>components/:</strong> Componentes reutilizables
                  </li>
                  <li>
                    <strong>auth/:</strong> Lógica de autenticación y contexto
                  </li>
                  <li>
                    <strong>public/:</strong> Archivos estáticos y assets
                  </li>
                </ul>
              </>
            )}

            {activeSection === "api" && (
              <>
                <h2>API Endpoints</h2>
                <p>A continuación se detallan todos los endpoints disponibles en el backend:</p>

                <h3>Autenticación</h3>
                <div className="endpoint">
                  <span className="endpoint-method method-post">POST</span>
                  <span className="endpoint-url">/api/auth/login</span>
                </div>
                <p>Autentica un usuario y retorna un token JWT.</p>
                <div className="code-block">
                  <code>{`Request:
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "success": true,
  "token": "eyJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com"
  }
}`}</code>
                </div>

                <h3>Rutas</h3>
                <div className="endpoint">
                  <span className="endpoint-method method-get">GET</span>
                  <span className="endpoint-url">/api/routes</span>
                </div>
                <p>Obtiene todas las rutas disponibles.</p>

                <div className="endpoint">
                  <span className="endpoint-method method-post">POST</span>
                  <span className="endpoint-url">/api/routes</span>
                </div>
                <p>Crea una nueva ruta.</p>

                <div className="endpoint">
                  <span className="endpoint-method method-put">PUT</span>
                  <span className="endpoint-url">/api/routes/:id</span>
                </div>
                <p>Actualiza una ruta existente.</p>

                <div className="endpoint">
                  <span className="endpoint-method method-delete">DELETE</span>
                  <span className="endpoint-url">/api/routes/:id</span>
                </div>
                <p>Elimina una ruta.</p>
              </>
            )}

            {activeSection === "json" && (
              <>
                <h2>Formato JSON</h2>
                <p>Los datos se intercambian en formato JSON. Aquí están los principales esquemas:</p>

                <h3>Objeto Ruta</h3>
                <div className="code-block">
                  <code>{`{
  "id": 1,
  "name": "Ruta Centro - Parque",
  "description": "Ruta por el centro urbano",
  "distance": 12.5,
  "elevation_gain": 145,
  "elevation_loss": 142,
  "terrain_type": "urban",
  "difficulty": "moderate",
  "estimated_time": 45,
  "waypoints": [
    {
      "lat": -33.8688,
      "lng": -56.1635,
      "elevation": 25
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}`}</code>
                </div>

                <h3>Objeto Bicicleta Eléctrica</h3>
                <div className="code-block">
                  <code>{`{
  "id": 1,
  "model": "E-Trek Pro 2024",
  "motor_power": 750,
  "battery_capacity": 540,
  "weight": 22.5,
  "efficiency": 0.85,
  "max_speed": 45,
  "range": 120
}`}</code>
                </div>

                <div className="note">
                  <p>
                    <strong>Nota:</strong> Todos los valores numéricos se envían en unidades del Sistema Internacional
                    (SI).
                  </p>
                </div>
              </>
            )}

            {activeSection === "autenticacion" && (
              <>
                <h2>Autenticación</h2>
                <p>El sistema utiliza JWT (JSON Web Tokens) para autenticación.</p>

                <h3>Flujo de autenticación</h3>
                <ol>
                  <li>El usuario proporciona email y contraseña</li>
                  <li>El servidor valida las credenciales</li>
                  <li>Se genera un token JWT válido por 24 horas</li>
                  <li>El cliente almacena el token en localStorage</li>
                  <li>Todos los requests posteriores incluyen el token en el header Authorization</li>
                </ol>

                <h3>Uso del token</h3>
                <div className="code-block">
                  <code>{`fetch('/api/routes', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer eyJhbGc...',
    'Content-Type': 'application/json'
  }
})`}</code>
                </div>

                <div className="note">
                  <p>
                    <strong>Importante:</strong> Siempre incluye el token en el header Authorization para requests
                    autenticados.
                  </p>
                </div>
              </>
            )}

            {activeSection === "ejemplos" && (
              <>
                <h2>Ejemplos de Uso</h2>

                <h3>Crear una nueva ruta</h3>
                <div className="code-block">
                  <code>{`const createRoute = async (routeData) => {
  const response = await fetch('/api/routes', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'Mi Ruta',
      distance: 15.3,
      elevation_gain: 200,
      terrain_type: 'mountain',
      difficulty: 'hard'
    })
  });
  return await response.json();
};`}</code>
                </div>

                <h3>Simular consumo energético</h3>
                <div className="code-block">
                  <code>{`const calculateEnergyConsumption = (
  distance,
  elevationGain,
  motorPower,
  efficiency
) => {
  const energyRequired = (distance * 0.1 + elevationGain * 0.005) 
    / efficiency;
  return energyRequired;
};

// Ejemplo:
const consumption = calculateEnergyConsumption(15, 200, 750, 0.85);
console.log(\`Consumo estimado: \${consumption.toFixed(2)} Wh\`);`}</code>
                </div>

                <h3>Obtener rutas del usuario</h3>
                <div className="code-block">
                  <code>{`const getUserRoutes = async (userId) => {
  const response = await fetch(\`/api/routes?user_id=\${userId}\`, {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer ' + token
    }
  });
  const routes = await response.json();
  return routes.filter(r => r.distance > 5);
};`}</code>
                </div>
              </>
            )}
          </main>
        </div>
      </div>
    </>
  )
}