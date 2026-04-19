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

const YEARS = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

export default function App() {
  const [stations, setStations] = useState([])
  const [selected, setSelected] = useState(null)
  const [history, setHistory] = useState([])
  const [yearFrom, setYearFrom] = useState(2013)
  const [yearTo, setYearTo] = useState(2024)
  const [loading, setLoading] = useState(false)

  const fetchStations = () => {
    setLoading(true)
    fetch(`${API}/map?year_from=${yearFrom}&year_to=${yearTo}`)
      .then(r => r.json())
      .then(data => { setStations(data); setLoading(false) })
      .catch(console.error)
  }

  useEffect(() => { fetchStations() }, [])

  const onStationClick = (station) => {
    setSelected(station)
    fetch(`${API}/station/${station.station_id}`)
      .then(r => r.json())
      .then(setHistory)
      .catch(console.error)
  }

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: 1 }}>
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
                  Type: {s.station_type}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div style={{
        width: 360,
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border)',
        padding: '1rem',
        overflowY: 'auto',
      }}>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 500, marginBottom: '0.5rem' }}>
          EU Air Quality
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1rem' }}>
          {stations.length} stations · {yearFrom}–{yearTo}
        </p>

        <div style={{
          display: 'flex', gap: '0.5rem', alignItems: 'center',
          marginBottom: '1.5rem',
        }}>
          <select
            value={yearFrom}
            onChange={e => setYearFrom(Number(e.target.value))}
            style={{
              flex: 1, padding: '0.4rem',
              background: 'var(--bg-card)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 4,
              fontSize: '0.8rem',
            }}
          >
            {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>to</span>
          <select
            value={yearTo}
            onChange={e => setYearTo(Number(e.target.value))}
            style={{
              flex: 1, padding: '0.4rem',
              background: 'var(--bg-card)', color: 'var(--text-primary)',
              border: '1px solid var(--border)', borderRadius: 4,
              fontSize: '0.8rem',
            }}
          >
            {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
          <button
            onClick={fetchStations}
            disabled={loading}
            style={{
              padding: '0.4rem 0.8rem',
              background: 'var(--accent)', color: '#fff',
              border: 'none', borderRadius: 4,
              cursor: 'pointer', fontSize: '0.8rem',
              opacity: loading ? 0.5 : 1,
            }}
          >
            {loading ? '...' : 'Go'}
          </button>
        </div>

        {selected ? (
          <div>
            <h2 style={{ fontSize: '1rem', marginBottom: '0.25rem' }}>
              {selected.station_name}
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
              {selected.country} · {selected.area_type} · {selected.station_type}
            </p>
            <div style={{
              fontSize: '2rem', fontWeight: 500,
              color: aqiColor(selected.avg_aqi), margin: '1rem 0',
            }}>
              AQI {Math.round(selected.avg_aqi)}
            </div>

            {history.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
                  Last {history.length} days
                </p>
                <div style={{
                  display: 'flex', gap: 1, height: 60, alignItems: 'flex-end',
                }}>
                  {history.map((d, i) => (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        height: `${Math.min(100, (d.aqi / 200) * 100)}%`,
                        background: aqiColor(d.aqi),
                        opacity: 0.7,
                        borderRadius: '1px 1px 0 0',
                      }}
                      title={`${d.date}: AQI ${Math.round(d.aqi)}`}
                    />
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => { setSelected(null); setHistory([]) }}
              style={{
                marginTop: '1rem', padding: '0.4rem 0.8rem',
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
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
              Click a station on the map
            </p>
            <div style={{ marginTop: '1rem' }}>
              {[
                { label: 'Good', color: '#22c55e', range: '0-50' },
                { label: 'Moderate', color: '#eab308', range: '51-100' },
                { label: 'Unhealthy (SG)', color: '#f97316', range: '101-150' },
                { label: 'Unhealthy', color: '#ef4444', range: '151-200' },
                { label: 'Very Unhealthy', color: '#a855f7', range: '201-300' },
                { label: 'Hazardous', color: '#7c1d1d', range: '301+' },
              ].map(item => (
                <div key={item.label} style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  marginBottom: '0.3rem', fontSize: '0.75rem',
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
