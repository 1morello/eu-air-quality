import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const API = 'http://localhost:8000'

const aqiColor = (aqi) => {
  if (aqi <= 50) return '#22c55e'
  if (aqi <= 100) return '#eab308'
  if (aqi <= 150) return '#f97316'
  if (aqi <= 200) return '#ef4444'
  if (aqi <= 300) return '#a855f7'
  return '#7c1d1d'
}

const aqiLabel = (aqi) => {
  if (aqi <= 50) return 'Good'
  if (aqi <= 100) return 'Moderate'
  if (aqi <= 150) return 'Unhealthy (SG)'
  if (aqi <= 200) return 'Unhealthy'
  if (aqi <= 300) return 'Very Unhealthy'
  return 'Hazardous'
}

const PERIODS = ['recent', '2025', '2024', '2023', '2022', 'all']

const chipStyle = (active) => ({
  padding: '0.35rem 0.7rem',
  background: active ? 'var(--accent)' : 'var(--bg-card)',
  color: active ? '#fff' : 'var(--text-secondary)',
  border: '1px solid var(--border)',
  borderRadius: 20,
  cursor: 'pointer',
  fontSize: '0.75rem',
  whiteSpace: 'nowrap',
})

export default function App() {
  const [stations, setStations] = useState([])
  const [selected, setSelected] = useState(null)
  const [history, setHistory] = useState([])
  const [prediction, setPrediction] = useState(null)
  const [period, setPeriod] = useState('recent')
  const [loading, setLoading] = useState(false)

  const fetchStations = (p) => {
    setLoading(true)
    fetch(`${API}/map?period=${p}`)
      .then(r => r.json())
      .then(data => { setStations(data); setLoading(false) })
      .catch(console.error)
  }

  useEffect(() => { fetchStations(period) }, [period])

  const onStationClick = (station) => {
    setSelected(station)
    setPrediction(null)

    fetch(`${API}/station/${station.station_id}`)
      .then(r => r.json())
      .then(setHistory)
      .catch(console.error)

    fetch(`${API}/predict/${station.station_id}`)
      .then(r => r.json())
      .then(setPrediction)
      .catch(console.error)
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={[48.5, 8]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap &copy; CARTO'
          />
          {stations.map(s => (
            <CircleMarker
              key={s.station_id}
              center={[s.lat, s.lon]}
              radius={4}
              fillColor={aqiColor(s.avg_aqi)}
              fillOpacity={0.8}
              stroke={false}
              eventHandlers={{ click: () => onStationClick(s) }}
            >
              <Popup>
                <div style={{ color: '#000', fontSize: '0.8rem' }}>
                  <strong>{s.station_name}</strong><br />
                  AQI: {s.avg_aqi}<br />
                  {s.station_type}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Period chips overlay */}
        <div style={{
          position: 'absolute', top: 12, left: 60, zIndex: 1000,
          display: 'flex', gap: '0.35rem',
        }}>
          {PERIODS.map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              style={chipStyle(period === p)}
            >
              {p === 'recent' ? 'Last 30 days' : p === 'all' ? 'All time' : p}
            </button>
          ))}
          {loading && (
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', padding: '0.35rem' }}>
              Loading...
            </span>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <div style={{
        width: 360,
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border)',
        padding: '1.25rem',
        overflowY: 'auto',
      }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 500, marginBottom: '0.25rem' }}>
          EU Air Quality
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.5rem' }}>
          {stations.length} stations
        </p>

        {selected ? (
          <div>
            <h2 style={{ fontSize: '1.05rem', marginBottom: '0.2rem' }}>
              {selected.station_name}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
              {selected.country} · {selected.area_type} · {selected.station_type}
            </p>

            {/* Today + Tomorrow blocks */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              {/* Today */}
              <div style={{
                flex: 1, padding: '0.75rem',
                background: 'var(--bg-card)', borderRadius: 8,
                borderTop: `3px solid ${aqiColor(prediction?.current_aqi || selected.avg_aqi)}`,
              }}>
                <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                  Today
                </p>
                <div style={{
                  fontSize: '1.5rem', fontWeight: 500,
                  color: aqiColor(prediction?.current_aqi || selected.avg_aqi),
                }}>
                  {Math.round(prediction?.current_aqi || selected.avg_aqi)}
                </div>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                  {prediction?.current_category || aqiLabel(selected.avg_aqi)}
                </p>
              </div>

              {/* Tomorrow */}
              {prediction && !prediction.error && (
                <div style={{
                  flex: 1, padding: '0.75rem',
                  background: 'var(--bg-card)', borderRadius: 8,
                  borderTop: `3px solid ${aqiColor(prediction.aqi)}`,
                }}>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    Tomorrow
                  </p>
                  <div style={{
                    fontSize: '1.5rem', fontWeight: 500,
                    color: aqiColor(prediction.aqi),
                  }}>
                    {prediction.aqi}
                  </div>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    {prediction.category}
                  </p>
                </div>
              )}
            </div>

            {/* Mini chart */}
            {history.length > 0 && (() => {
              const data = history.filter(d => d.aqi > 0).slice(-90)
              return (
                <div style={{ marginBottom: '1rem' }}>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', marginBottom: '0.4rem' }}>
                    Last {data.length} days
                  </p>
                  <div style={{
                    display: 'flex', height: 50, alignItems: 'flex-end',
                  }}>
                    {data.map((d, i) => (
                      <div
                        key={i}
                        style={{
                          flex: 1,
                          height: `${Math.min(100, (d.aqi / 200) * 100)}%`,
                          background: aqiColor(d.aqi),
                          opacity: 0.7,
                          minWidth: 2,
                        }}
                        title={`${d.date}: AQI ${Math.round(d.aqi)}`}
                      />
                    ))}
                  </div>
                </div>
              )
            })()}

            <button
              onClick={() => { setSelected(null); setHistory([]); setPrediction(null) }}
              style={{
                padding: '0.4rem 0.8rem',
                background: 'var(--bg-card)', color: 'var(--text-secondary)',
                border: '1px solid var(--border)', borderRadius: 4,
                cursor: 'pointer', fontSize: '0.8rem',
              }}
            >
              ← Back
            </button>
          </div>
        ) : (
          <div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
              Click a station to see details and forecast
            </p>
            <div>
              {[
                { label: 'Good', color: '#22c55e', range: '0–50' },
                { label: 'Moderate', color: '#eab308', range: '51–100' },
                { label: 'Unhealthy (SG)', color: '#f97316', range: '101–150' },
                { label: 'Unhealthy', color: '#ef4444', range: '151–200' },
                { label: 'Very Unhealthy', color: '#a855f7', range: '201–300' },
                { label: 'Hazardous', color: '#7c1d1d', range: '301+' },
              ].map(item => (
                <div key={item.label} style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  marginBottom: '0.35rem', fontSize: '0.75rem',
                }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: item.color,
                  }} />
                  <span>{item.label}</span>
                  <span style={{ color: 'var(--text-secondary)', marginLeft: 'auto' }}>
                    {item.range}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
