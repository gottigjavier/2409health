import { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import "../bootstrap.css";
import { isAuthenticated, login as apiLogin, logout as apiLogout, getUser } from "../services/api";
import { appManager } from "../services/websocket";
import Sketch from "./rooms-beds-sketch/Sketch";
import CallsList from "./calls-list/CallsList";
import TasksList from "./tasks-list/TasksList";
import AppContext from "../context/appContext";
import favicon from "../nursing_favicon.ico";

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [, setAppState] = useContext(AppContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await apiLogin(username, password);
      setAppState({ loggedIn: true });
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <div className="row mt-4">
        <div className="col-4"></div>
        <div className="text-center col-4">
          <div className="brand-logo mb-3">
            <img src={favicon} alt="Logo" width="80" height="80" />
          </div>
          <h2>Iniciar Sesión</h2>
          {error && <div className="alert alert-danger">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <input
                autoFocus
                className="form-control"
                type="text"
                name="username"
                placeholder="Nombre de Usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            <div className="form-group">
              <input
                className="form-control"
                type="password"
                name="password"
                placeholder="Contraseña"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <input className="btn btn-primary" type="submit" value="Confirmar" />
          </form>
        </div>
        <div className="col-4"></div>
      </div>
      <br />
    </>
  );
}

export default Login;
