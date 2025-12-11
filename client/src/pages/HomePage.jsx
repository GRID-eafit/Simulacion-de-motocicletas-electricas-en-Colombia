"use client"

import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import BidEafitLogo from "../images/bid-eafit-logo.png"

// Imágenes de "Workshop: Motocicletas eléctricas en Colombia"
import Proyecto1 from "../images/proyecto1.jpg"
import Proyecto2 from "../images/proyecto2.jpg"
import Proyecto3 from "../images/proyecto3.jpg"
import Proyecto4 from "../images/proyecto4.jpg"
import Proyecto5 from "../images/proyecto5.jpg"
import Proyecto6 from "../images/proyecto6.jpg"
import Proyecto7 from "../images/proyecto7.jpg"
import Proyecto8 from "../images/proyecto8.jpg"
import Proyecto9 from "../images/proyecto9.jpg"
import Proyecto10 from "../images/proyecto10.jpg"

export default function HomePage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState("simulation")
  const [projectIndex, setProjectIndex] = useState(0)
  const [fade, setFade] = useState(false)

  const simulationOptions = [
    {
      title: "¿Qué puedes hacer aquí?",
      items: [
        "Configurar tus simulaciones",
        "Seleccionar recorridos reales",
        "Analizar rendimiento",
        "Evaluar impacto ambiental",
      ],
    },
    {
      title: "Resultados que obtendrás",
      items: [
        "Velocidad promedio e instantánea",
        "Consumo energético total",
        "Emisiones estimadas de CO₂",
        "Tiempo total de recorrido",
        "Número de recargas",
        "Energía demandada por estación de carga",
      ],
    },
    {
      title: "Comienza tu simulación ahora",
      items: null,
      cta: true,
    },
  ]

  const telemetryOptions = [
    {
      title: "¿Qué puedes hacer aquí?",
      items: [
        "Supervisar en tiempo real",
        "Ver el recorrido actual en el mapa",
        "Analizar desempeño instantáneo",
      ],
    },
    {
      title: "Datos y visualizaciones",
      items: [
        "Estado de carga",
        "Velocidad actual",
        "Potencia (W) y voltaje (V)",
        "Tiempo total de recorrido",
        "Mapa con geolocalización dinámica",
      ],
    },
    {
      title: "Conecta un vehículo y comienza el monitoreo en vivo",
      items: null,
      cta: true,
    },
  ]

  const options = activeTab === "simulation" ? simulationOptions : telemetryOptions

  // Carrusel "Workshop: Motocicletas eléctricas en Colombia"
  const projectImages = [
    {
      src: Proyecto1,
      title:"",
      description:"Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto2,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto3,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto4,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto5,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto6,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto7,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto8,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto9,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
    {
      src: Proyecto10,
      title: "",
      description: "Se anazalizaron los roles, las oportunidades y los retos de las motocicletas eléctricas en la evolucion del transporte colombiano junto a actores clave del sector.",
    },
  ]

  const goNextProject = () => {
    setFade(true)
    setTimeout(() => {
      setProjectIndex((prev) => (prev + 1) % projectImages.length)
      setFade(false)
    }, 200)
  }

  const goPrevProject = () => {
    setFade(true)
    setTimeout(() => {
      setProjectIndex((prev) =>
        prev === 0 ? projectImages.length - 1 : prev - 1
      )
      setFade(false)
    }, 200)
  }

  // Auto-slide cada 4 segundos con fade
  useEffect(() => {
    const intervalId = setInterval(() => {
      setFade(true)
      setTimeout(() => {
        setProjectIndex((prev) => (prev + 1) % projectImages.length)
        setFade(false)
      }, 200)
    }, 4000)

    return () => clearInterval(intervalId)
  }, [])

  return (
    <main className="home-page">
      <style>{`
        .home-page {
          background: #f5f5f5;
          min-height: calc(100vh - 56px);
          padding: 40px 20px;
        }

        .home-container {
          max-width: 1400px; /* más ancho para que el carrusel respire */
          margin: 0 auto;
        }

        .hero-search {
          background: #ddd;
          border-radius: 20px;
          padding: 20px;
          margin-bottom: 30px;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .hero-search input {
          flex: 1;
          border: none;
          background: transparent;
          font-size: 16px;
          outline: none;
          color: #666;
        }

        .hero-search input::placeholder {
          color: #999;
        }

        .logo-img {
          width: 60px;
          height: 60px;
          background: white;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: #333;
        }

        .hero-question {
          font-size: 16px;
          color: #333;
        }

        .hero-divider {
          width: 1px;
          height: 100px;
          background: #aaa;
        }

        .hero-bid-logo {
          height: 150px;
          object-fit: contain;
        }

        .hero-logo-wrap {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .tabs-container {
          display: flex;
          gap: 12px;
          margin: 30px 0;
          justify-content: center;
        }

        .tab-btn {
          padding: 10px 24px;
          border: none;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          background: #999;
          color: white;
        }

        .tab-btn.active {
          background: #000;
        }

        .section-header {
          text-align: center;
          margin: 40px 0;
        }

        .section-header h2 {
          font-size: 24px;
          font-weight: 800;
          margin-bottom: 8px;
          color: #000;
        }

        .section-header p {
          color: #666;
          font-size: 14px;
          line-height: 1.6;
          max-width: 800px;
          margin: 0 auto;
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
          margin-bottom: 40px;
        }

        @media (max-width: 1024px) {
          .options-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .options-grid {
            grid-template-columns: 1fr;
          }
        }

        .option-card {
          background: #000;
          border-radius: 20px;
          padding: 24px;
          color: white;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .option-title {
          text-align: center;
          width: 100%;
        }

        .option-card h3 {
          font-size: 18px;
          font-weight: 700;
          margin: 0;
        }

        .option-card ul {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .option-card li {
          font-size: 14px;
          color: #eee;
          padding: 8px 12px;
          background: #1a1a1a;
          border-radius: 10px;
          text-align: center;
        }

        .option-card.cta {
          justify-content: center;
          align-items: center;
          text-align: center;
          gap: 20px;
        }

        .option-card.cta h3 {
          font-size: 16px;
        }

        .option-card.cta p {
          font-size: 13px;
          color: #bbb;
          margin: 0;
          line-height: 1.5;
        }

        .cta-button {
          background: #2563eb;
          color: white;
          border: none;
          padding: 12px 32px;
          border-radius: 50px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          align-self: center;
        }

        .cta-button:hover {
          background: #1d4ed8;
          transform: translateY(-2px);
        }

        /* === Sección inferior (Acerca del proyecto / Workshop: Motocicletas eléctricas en Colombia / Contáctanos) === */
        .bottom-section {
          max-width: 1400px;
          margin: 40px auto 60px;
          display: grid;
          grid-template-columns: 3fr 2fr; /* más espacio horizontal para carrusel */
          gap: 32px;
        }

        @media (max-width: 768px) {
          .bottom-section {
            grid-template-columns: 1fr;
          }
        }

        .bottom-card,
        .contact-card {
          background: #ddd;
          border-radius: 20px;
          padding: 32px 40px;
          color: #555;
        }

        .bottom-card {
          min-height: 220px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .card-title {
          font-size: 16px;
          font-weight: 600;
          margin: 0 0 12px 0;
        }

        .about-card {
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .about-card p {
          margin: 0;
          font-size: 14px;
          line-height: 1.6;
          max-width: 90%;
        }

        .center-card {
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .contact-card {
          grid-column: 1 / -1;
          text-align: center;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 15px;
          font-weight: 500;
        }

        /* === Carrusel "Workshop: Motocicletas eléctricas en Colombia" === */
        .projects-card {
          padding: 24px 32px;
        }

        .projects-carousel {
          width: 100%;
          max-width: 800px; /* más ancho */
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
        }

        .projects-image-wrapper {
          position: relative;
          width: 100%;
          height: 400px; /* más alto, evita recortes */
          border-radius: 20px;
          overflow: hidden;
          background: #cfcfcf;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .projects-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
          transition: opacity 0.5s ease-in-out;
          opacity: 1;
        }

        .projects-image.fade {
          opacity: 0;
        }

        .carousel-btn {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          border: none;
          background: rgba(0, 0, 0, 0.45);
          color: white;
          width: 36px;
          height: 36px;
          border-radius: 999px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 22px;
          cursor: pointer;
          transition: background 0.2s ease, transform 0.1s ease;
        }

        .carousel-btn.prev {
          left: 12px;
        }

        .carousel-btn.next {
          right: 12px;
        }

        .carousel-btn:hover {
          background: rgba(0, 0, 0, 0.7);
          transform: translateY(-50%) scale(1.05);
        }

        .projects-caption {
          text-align: center;
        }

        .projects-caption h4 {
          margin: 0 0 4px 0;
          font-size: 15px;
          font-weight: 600;
          color: #333;
        }

        .projects-caption p {
          margin: 0;
          font-size: 13px;
          color: #666;
        }

        .carousel-dots {
          display: flex;
          gap: 6px;
          margin-top: 4px;
        }

        .carousel-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          border: none;
          background: #bbb;
          cursor: pointer;
          transition: transform 0.15s ease, background 0.15s ease;
        }

        .carousel-dot.active {
          background: #111;
          transform: scale(1.3);
        }
      `}</style>

      <div className="home-container">
        {/* Hero Search */}
        <div className="hero-search">
          <span className="hero-question">¿Qué hace esta plataforma?</span>
          <div className="hero-divider" />
          <div className="hero-logo-wrap">
            <img
              src={BidEafitLogo}
              alt="Proyecto BID - EAFIT"
              className="hero-bid-logo"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-container">
          <button
            className={`tab-btn ${activeTab === "simulation" ? "active" : ""}`}
            onClick={() => setActiveTab("simulation")}
          >
            Simulación
          </button>
          <button
            className={`tab-btn ${activeTab === "telemetry" ? "active" : ""}`}
            onClick={() => setActiveTab("telemetry")}
          >
            Telemetría
          </button>
        </div>

        {/* Section Header */}
        <div className="section-header">
          <h2>
            {activeTab === "simulation"
              ? "Simula el comportamiento real de motocicletas en entornos urbanos"
              : "Monitorea el rendimiento y estado de tu motocicleta en tiempo real"}
          </h2>
          <p>
            {activeTab === "simulation"
              ? "Explora cómo diferentes tipos de motocicletas afectan la contaminación de aire en contextos urbanos y geográficos. Ajusta parámetros, ejecuta simulaciones y analiza resultados técnicos y ambientales."
              : "Visualiza los datos operacionales de cada vehículo conectado. Ubicación, energía, velocidad y desempeño. La telemetría te permite entender cómo se comportan tus motocicletas en condiciones reales de operación."}
          </p>
        </div>

        {/* Options Grid */}
        <div className="options-grid">
          {options.map((option, idx) => (
            <div key={idx} className={`option-card ${option.cta ? "cta" : ""}`}>
              <h3 className="option-title">{option.title}</h3>

              {option.items ? (
                <ul>
                  {option.items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              ) : (
                <>
                  <p>
                    {activeTab === "simulation"
                      ? "Ajusta tus parámetros, visualiza la ruta en el mapa y observa cómo impacta el consumo y las emisiones."
                      : "Observa cada sensor en tiempo real. Toma decisiones informadas sobre operación y emisiones."}
                  </p>
                  <button
                    className="cta-button"
                    onClick={() =>
                      navigate(
                        activeTab === "simulation" ? "/mapa" : "/telemetry"
                      )
                    }
                  >
                    {activeTab === "simulation"
                      ? "Iniciar simulación"
                      : "Iniciar Telemetría"}
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Bottom Cards */}
        <div className="bottom-section">
          {/* Acerca del proyecto */}
          <div className="bottom-card about-card">
            <h3 className="card-title">Acerca del proyecto</h3>
            <p>
              Este proyecto tiene como finalidad realizar un análisis de los indicadores de impacto en los
              aspectos técnicos, socioeconómicos y ambientales resultantes de la prevista introducción de
              motocicletas eléctricas o híbridas de bajo cilindraje en el sector del transporte colombiano.
              La determinación de las variables a considerar en este estudio y de los indicadores se
              fundamentará en análisis sistemáticos y descriptivos de casos, además de la información
              pertinente disponible en bases de datos, literatura científica y reportes comerciales. Esta
              información se empleará para realizar una caracterización detallada de los grupos de interés
              del sector motociclista colombiano y para definir tres zonas de estudio dentro del territorio
              colombiano, en las cuales se evaluarán los indicadores de impacto mediante la simulación de
              escenarios y la experimentación con vehículos. Posteriormente, los hallazgos de la
              experimentación y la simulación se aplicarán en la elaboración de estrategias orientadas a
              facilitar la transición hacia una movilidad sostenible, reducir las brechas existentes en el
              acceso a nuevas tecnologías de movilidad, fortalecer las políticas públicas y descubrir
              oportunidades para el desarrollo económico y la generación de empleo.
            </p>
          </div>

          {/* Workshop: Motocicletas eléctricas en Colombia con carrusel */}
          <div className="bottom-card center-card projects-card">
            <div className="projects-carousel">
              <h3 className="card-title">Workshop: Motocicletas eléctricas en Colombia</h3>

              <div className="projects-image-wrapper">
                <button
                  className="carousel-btn prev"
                  onClick={goPrevProject}
                  aria-label="Proyecto anterior"
                >
                  ‹
                </button>

                <img
                  src={projectImages[projectIndex].src}
                  alt={projectImages[projectIndex].title}
                  className={`projects-image ${fade ? "fade" : ""}`}
                />

                <button
                  className="carousel-btn next"
                  onClick={goNextProject}
                  aria-label="Proyecto siguiente"
                >
                  ›
                </button>
              </div>

              <div className="projects-caption">
                <h4>{projectImages[projectIndex].title}</h4>
                <p>{projectImages[projectIndex].description}</p>
              </div>

              <div className="carousel-dots">
                {projectImages.map((_, i) => (
                  <button
                    key={i}
                    className={`carousel-dot ${
                      i === projectIndex ? "active" : ""
                    }`}
                    onClick={() => setProjectIndex(i)}
                    aria-label={`Ir al proyecto ${i + 1}`}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Contáctanos */}
        </div>
      </div>
    </main>
  )
}