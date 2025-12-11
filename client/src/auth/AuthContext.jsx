import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

// Mock database de usuarios para demo
const DEMO_USERS = {
  admin: "password",
  user: "password",
  test: "password",
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Verificar si hay sesión guardada al cargar
  useEffect(() => {
    const savedUser = localStorage.getItem("auth_user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  // Función de login
  const login = (username, password) => {
    // Validar credenciales (demo: cualquier usuario con password "password" funciona)
    if (password === "password" && username.trim()) {
      const newUser = {
        id: username,
        username: username,
        email: `${username}@example.com`,
      };

      setUser(newUser);
      setIsAuthenticated(true);
      localStorage.setItem("auth_user", JSON.stringify(newUser));
      return true;
    }

    return false;
  };

  // Función de logout
  const logout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem("auth_user");
  };

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}