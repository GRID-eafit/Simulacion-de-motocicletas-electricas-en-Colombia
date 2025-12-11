import React, { createContext, useContext, useState } from "react";

/**
 * Shim de Tabs robusto:
 * - Usa contexto para manejar el valor activo.
 * - TabsList solo envuelve; TabsTrigger pinta el botón y cambia el valor.
 * - TabsContent muestra su contenido si value coincide.
 */

const TabsCtx = createContext({ value: "", setValue: () => {} });

export function Tabs({ defaultValue, children, className = "" }) {
  const [value, setValue] = useState(defaultValue);
  return (
    <TabsCtx.Provider value={{ value, setValue }}>
      <div className={className}>{children}</div>
    </TabsCtx.Provider>
  );
}

export function TabsList({ children, className = "" }) {
  return <div className={className} role="tablist">{children}</div>;
}

export function TabsTrigger({ value, children }) {
  const { value: active, setValue } = useContext(TabsCtx);
  const isActive = active === value;
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => setValue(value)}
      className={`px-3 py-1 rounded-2xl border ${
        isActive ? "bg-black text-white" : "hover:bg-gray-50"
      }`}
      style={{ marginRight: 8 }}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children, className = "" }) {
  const { value: active } = useContext(TabsCtx);
  if (active !== value) return null;
  return <div className={className}>{children}</div>;
}