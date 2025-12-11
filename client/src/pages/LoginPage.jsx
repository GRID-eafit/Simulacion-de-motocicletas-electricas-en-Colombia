"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import TopNav from "../components/layout/TopNav"
import Footer from "../components/layout/Footer"

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [user, setUser] = useState("")
  const [pass, setPass] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    setTimeout(() => {
      const ok = login(user, pass)

      if (!ok) {
        setError("Usuario o contraseña inválidos")
        setIsLoading(false)
        return
      }

      navigate("/home", { replace: true })
    }, 300)
  }

  const styles = `
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }

    .login-wrapper {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      background: #f5f5f5;
    }

    .login-content {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 40px 20px;
    }

    /* Updated login container to match Figma design */
    .login-container {
      width: 100%;
      max-width: 500px;
    }

    .login-card {
      background: #d4d4d4;
      border-radius: 20px;
      width: 100%;
      padding: 60px 50px;
      animation: slideUp 0.4s ease-out;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 30px;
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .login-header {
      text-align: center;
      width: 100%;;
    }

    .login-header-icon {
      width: 60px;
      height: 60px;
      background: black;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 32px;
      margin: 0 auto 20px;
    }

    .login-header h1 {
      font-size: 24px;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 8px;
    }

    .login-header p {
      font-size: 14px;
      color: #666;
      font-weight: 500;
    }

    .form-container {
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .form-group label {
      font-size: 13px;
      font-weight: 600;
      color: #333;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .form-group input {
      padding: 14px 16px;
      border: 2px solid #999;
      border-radius: 8px;
      font-size: 15px;
      transition: all 0.2s ease;
      background: white;
      color: #1a1a1a;
      font-family: inherit;
    }

    .form-group input::placeholder {
      color: #999;
    }

    .form-group input:focus {
      outline: none;
      border-color: #1a1a1a;
      box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.1);
    }

    .form-group input:hover {
      border-color: #666;
    }

    .error-message {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 14px;
      background: #fee;
      border: 1px solid #fcc;
      border-radius: 8px;
      color: #c33;
      font-size: 14px;
      font-weight: 500;
      animation: shake 0.3s ease;
    }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }

    .error-message::before {
      content: '⚠';
      font-weight: bold;
    }

    .submit-button {
      width: 100%;
      padding: 14px 16px;
      background: #000;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      position: relative;
      overflow: hidden;
    }

    .submit-button:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
      background: #1a1a1a;
    }

    .submit-button:active:not(:disabled) {
      transform: translateY(0);
    }

    .submit-button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .button-text {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .login-footer {
      text-align: center;
      font-size: 13px;
      color: #666;
      width: 100%;
    }

    .login-footer a {
      color: #1a1a1a;
      text-decoration: none;
      font-weight: 600;
      transition: color 0.2s;
    }

    .login-footer a:hover {
      color: #333;
      text-decoration: underline;
    }

    .form-links {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      color: #666;
    }

    .form-links a {
      color: #666;
      text-decoration: none;
      transition: color 0.2s;
    }

    .form-links a:hover {
      color: #1a1a1a;
    }

    @media (max-width: 640px) {
      .login-card {
        padding: 40px 30px;
        border-radius: 16px;
      }

      .login-header h1 {
        font-size: 20px;
      }

      .submit-button {
        padding: 12px 14px;
        font-size: 14px;
      }
    }
  `

  return (
    <>
      <style>{styles}</style>
      <div className="login-wrapper">
        <TopNav />
        <div className="login-content">
          <div className="login-container">
            {error && (
              <div className="error-message" style={{ marginBottom: "20px" }}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="login-card">
                <div className="login-header">
                  <div className="login-header-icon">👤</div>
                  <h1>Inicio Sesion</h1>
                </div>

                <div className="form-container">
                  <div className="form-group">
                    <label htmlFor="username">Usuario</label>
                    <input
                      id="username"
                      type="text"
                      placeholder="Usuario"
                      value={user}
                      onChange={(e) => setUser(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="password">Contraseña</label>
                    <input
                      id="password"
                      type="password"
                      placeholder="Contraseña"
                      value={pass}
                      onChange={(e) => setPass(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>

                  <button type="submit" className="submit-button" disabled={isLoading || !user || !pass}>
                    <span className="button-text">
                      {isLoading && <span className="spinner"></span>}
                      {isLoading ? "Ingresando..." : "Entrar"}
                    </span>
                  </button>
                </div>

                <div className="login-footer">
                  <div style={{ marginBottom: "8px" }}>
                    <a href="#">¿Olvidaste tu contraseña?</a>
                  </div>
                  <div>
                    ¿No tienes cuenta? <a href="#">Crear cuenta</a>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </div>
        <Footer />
      </div>
    </>
  )
}