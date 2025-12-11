export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-row">
        <span className="footer-title">Nuestras sedes</span>
        <span className="footer-contact">
          <strong>Línea nacional:</strong> 01 8000 515 900
        </span>
        <span className="footer-contact">
          <strong>WhatsApp:</strong> (57) 310 899 2908
        </span>
      </div>

      <div className="footer-divider"></div>

      <div className="footer-row footer-row-bottom">
        <span className="footer-branch">EAFIT Medellín</span>
        <span className="footer-branch">EAFIT Pereira</span>
        <span className="footer-branch">EAFIT Bogotá</span>
        <span className="footer-branch">EAFIT Llanogrande</span>
      </div>
    </footer>
  );
}
