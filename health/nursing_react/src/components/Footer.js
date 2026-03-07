import { useContext } from "react";
import { useNavigate } from "react-router-dom";
import { logout as apiLogout, getUser } from "../services/api";
import AppContext from "../context/appContext";
import "./footer.css";

function Footer() {
  const navigate = useNavigate();
  const [appState] = useContext(AppContext);
  
  const user = getUser();
  const bedsOccupied = appState?.beds ? appState.beds.filter(bed => bed.bed_active).length : 0;

  const handleLogout = async () => {
    if (window.confirm("¿Está seguro de que desea cerrar sesión?")) {
      apiLogout();
      navigate("/login");
    }
  };

  return (
    <footer className="app-footer">
      <div className="footer-content">
        <div className="footer-section">
          <span className="footer-label">Usuario:</span>
          <span className="footer-value">{user?.username || "Anónimo"}</span>
        </div>
        
        <div className="footer-section">
          <span className="footer-label">Camas Ocupadas:</span>
          <span className="footer-value">{bedsOccupied}</span>
        </div>

        <div className="footer-section">
          <button
            className="btn btn-sm btn-danger"
            onClick={handleLogout}
            title="Cerrar sesión"
          >
            Logout
          </button>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
