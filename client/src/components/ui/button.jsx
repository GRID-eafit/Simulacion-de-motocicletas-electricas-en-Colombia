export function Button({ variant = "default", size = "md", className = "", ...props }) {
  const base = "inline-flex items-center justify-center rounded-2xl transition px-3 py-2";
  const styles = {
    default: "bg-black text-white hover:opacity-90",
    outline: "border hover:bg-gray-50",
    ghost: "hover:bg-gray-100",
  };
  return <button className={`${base} ${styles[variant]||styles.default} ${className}`} {...props} />;
}