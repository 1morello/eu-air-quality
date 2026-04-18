import { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

export default function App() {
  const [countries, setCountries] = useState([])
  const [selected, setSelected] = useState(null)
  const [stations, setStations] = useState([])

  useEffect(() => {
    fetch(`${API}/countries`)
      .then(r => r.json())
      .then(setCountries)
      .catch(console.error)
  }, [])

  useEffect(() => {
    if (!selected) return
    fetch(`${API}/stations?country=${selected}`)
      .then(r => r.json())
      .then(setStations)
      .catch(console.error)
  }, [selected])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1rem' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 500 }}>
          EU Air Quality
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          {countries.reduce((s, c) => s + c.stations, 0)} stations across {countries.length} countries
        </p>
      </header>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem' }}>
        {countries.map(c => (
          <button
            key={c.country}
            onClick={() => setSelected(c.country)}
            style={{
              padding: '0.5rem 1rem',
              background: selected === c.country ? 'var(--accent)' : 'var(--bg-card)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            {c.country} ({c.stations})
          </button>
        ))}
      </div>

      {stations.length > 0 && (
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 8,
          border: '1px solid var(--border)',
          padding: '1rem',
        }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            {stations.length} stations in {selected}
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '0.75rem',
          }}>
            {stations.slice(0, 20).map(s => (
              <StationCard key={s.station_id} station={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StationCard({ station }) {
  const color = station.avg_aqi <= 50 ? 'var(--good)'
    : station.avg_aqi <= 100 ? 'var(--moderate)'
    : station.avg_aqi <= 150 ? 'var(--unhealthy-sg)'
    : 'var(--unhealthy)'

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      borderRadius: 6,
      padding: '0.75rem',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
        {station.station_id}
      </div>
      <div style={{ fontSize: '1.25rem', fontWeight: 500, color }}>
        AQI {Math.round(station.avg_aqi)}
      </div>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        {station.days} days of data
      </div>
    </div>
  )
}
