import './ResultsPanel.css';

const CATEGORY_COLORS = {
  Segura: '#2E7D32',
  Moderada: '#F9A825',
  Riesgosa: '#C62828',
};

const ResultsPanel = ({ routeData }) => {
  if (!routeData?.safe_route) return null;

  const { summary } = routeData.safe_route;
  const color = CATEGORY_COLORS[summary.category] || '#555';

  return (
    <div className="results-panel">
      <h3>Resultado</h3>

      <div className="score-box" style={{ borderColor: color }}>
        <span className="score-num" style={{ color }}>{summary.security_score}</span>
        <span className="score-cat" style={{ backgroundColor: color }}>{summary.category}</span>
      </div>

      <ul className="results-meta">
        <li><span>Distancia</span><strong>{(summary.distance_m / 1000).toFixed(2)} km</strong></li>
        <li><span>Tiempo a pie</span><strong>{summary.walk_time_min} min</strong></li>
      </ul>
    </div>
  );
};

export default ResultsPanel;
