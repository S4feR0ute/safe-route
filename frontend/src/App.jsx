import { Routes, Route } from 'react-router-dom';
import MapPage from './pages/MapPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ModerationPage from './pages/ModerationPage';

function App() {
  return (
    <Routes>
      {/* La ruta base '/' mostrará el mapa */}
      <Route path="/" element={<MapPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/moderador" element={<ModerationPage />} />
    </Routes>
  );
}

export default App;