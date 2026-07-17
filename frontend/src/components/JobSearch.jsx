import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { MapContainer, TileLayer, Marker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import CVPreview from './CVPreview'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow })

// ── Brand colors ──────────────────────────────────────────────
const C = {
  sarcelle:    '#0F766E',
  terreCuite:  '#D9633A',
  creme:       '#FBF8F3',
  ardoise:     '#2A2521',
  pointFort:   '#3B7A57',
  aTravailler: '#C88A2E',
  ecartFort:   '#B4443C',
}

// ── Top banner ────────────────────────────────────────────────
function TopBar({ keywords, setKeywords, region, setRegion, regions, isSearching, onSearch, onShowCV }) {
  const fileRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null)

  async function handleUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadMsg(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('http://localhost:8000/cv/import', { method: 'POST', body: form })
      if (!res.ok) throw new Error()
      setUploadMsg('CV importé ✓')
      setTimeout(() => setUploadMsg(null), 3000)
    } catch {
      setUploadMsg('Erreur import')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="shrink-0 h-14 bg-white border-b border-gray-200 flex items-center gap-3 px-4 shadow-sm">
      <form onSubmit={onSearch} className="flex items-center gap-2 flex-1">
        <input
          type="text"
          value={keywords}
          onChange={(e) => setKeywords(e.target.value)}
          placeholder="Poste recherché"
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 w-56"
          style={{ '--tw-ring-color': C.sarcelle }}
        />
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none"
        >
          {regions.map((r) => (
            <option key={r.code} value={r.code}>{r.libelle}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={isSearching || !keywords}
          className="text-white px-4 py-1.5 rounded-lg text-sm font-medium disabled:opacity-50 transition-opacity"
          style={{ background: C.sarcelle }}
        >
          {isSearching ? '...' : 'Rechercher'}
        </button>
      </form>

      <div className="flex items-center gap-2 shrink-0">
        {uploadMsg && <span className="text-xs" style={{ color: C.pointFort }}>{uploadMsg}</span>}
        <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="border border-gray-200 hover:bg-gray-50 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50"
        >
          {uploading ? 'Import...' : '↑ CV'}
        </button>
        <button
          onClick={onShowCV}
          className="border border-gray-200 hover:bg-gray-50 text-gray-600 px-3 py-1.5 rounded-lg text-xs font-medium"
        >
          Voir CV
        </button>
      </div>
    </div>
  )
}

// ── Offer card ────────────────────────────────────────────────
function OfferCard({ offer, ratio, onAnalyze, isAnalyzing, analysis }) {
  const [showLocation, setShowLocation] = useState(false)

  const pct      = Math.round(ratio * 100)
  // These fields come directly from the search results — always available
  const location = offer.lieuTravail?.libelle
  const contract = offer.typeContratLibelle ?? offer.typeContrat
  const salary   = offer.salaire?.libelle
  const xp       = offer.experienceLibelle
  const lat      = offer.lieuTravail?.latitude
  const lng      = offer.lieuTravail?.longitude

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-3">

      {/* Header */}
      <div className="flex justify-between items-start gap-3">
        <div className="min-w-0">
          <h3 className="font-bold text-base leading-tight" style={{ color: C.ardoise }}>
            {offer.intitule}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {offer.entreprise?.nom ?? '—'}
            {contract ? ` · ${contract}` : ''}
            {xp       ? ` · ${xp}`       : ''}
            {salary   ? ` · ${salary}`   : ''}
          </p>
        </div>
        {offer.score != null && (
          <span
            className="text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 whitespace-nowrap"
            style={{ background: `${C.sarcelle}18`, color: C.sarcelle }}
          >
            match {pct}%
          </span>
        )}
      </div>

      {/* Location toggle */}
      {location && (
        <div>
          <button
            onClick={() => setShowLocation((v) => !v)}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            <span>📍</span>
            <span>{location}</span>
            <span className="ml-1">{showLocation ? '▲' : '▼'}</span>
          </button>

          {showLocation && lat && lng && (
            <div className="mt-2 rounded-xl overflow-hidden h-40 border border-gray-100">
              <MapContainer
                center={[lat, lng]}
                zoom={12}
                className="h-full w-full"
                zoomControl={false}
                scrollWheelZoom={false}
              >
                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <Marker position={[lat, lng]} />
              </MapContainer>
            </div>
          )}
          {showLocation && (!lat || !lng) && (
            <p className="mt-1 text-xs text-gray-400">Coordonnées non disponibles.</p>
          )}
        </div>
      )}

      {/* GitHub matches */}
      {offer.github_matches?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {offer.github_matches.map((repo) => (
            <span
              key={repo}
              className="text-xs px-2.5 py-0.5 rounded-full font-medium"
              style={{ background: `${C.pointFort}18`, color: C.pointFort }}
            >
              {repo}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          className="text-white text-xs font-medium px-4 py-2 rounded-lg transition-opacity hover:opacity-90"
          style={{ background: C.terreCuite }}
        >
          Générer la lettre
        </button>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing || !!analysis}
          className="text-xs font-medium px-4 py-2 rounded-lg border transition-colors disabled:opacity-50"
          style={{ borderColor: C.sarcelle, color: C.sarcelle }}
        >
          {isAnalyzing ? 'Analyse...' : analysis ? 'Analysé ✓' : "Analyser l'écart"}
        </button>
      </div>

      {/* Analysis result */}
      {analysis && (
        <div
          className="text-xs rounded-xl p-3 prose prose-xs"
          style={{ background: C.creme, color: C.ardoise }}
        >
          <ReactMarkdown>{analysis}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

// ── Right chat column ─────────────────────────────────────────
function ChatColumn() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  async function sendMessage() {
    if (!input.trim() || isLoading) return
    const userMsg = { role: 'user', content: input }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setInput('')
    setIsLoading(true)
    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, history: messages }),
      })
      const data = await res.json()
      setMessages([...updated, { role: 'assistant', content: data.response }])
    } catch {
      setMessages([...updated, { role: 'assistant', content: 'Erreur de connexion.' }])
    } finally {
      setIsLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="w-80 shrink-0 h-full flex flex-col bg-white border-l border-gray-200">
      <div className="px-4 py-3 border-b border-gray-100">
        <p className="text-sm font-semibold" style={{ color: C.ardoise }}>Assistant IA</p>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {messages.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-8">
            Posez une question sur vos recherches ou votre candidature.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] px-3 py-2 rounded-xl text-xs prose prose-xs`}
              style={msg.role === 'user'
                ? { background: C.sarcelle, color: 'white' }
                : { background: C.creme, color: C.ardoise }}
            >
              {msg.role === 'assistant'
                ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                : msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-3 py-2 rounded-xl text-xs" style={{ background: C.creme, color: C.ardoise }}>
              ...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-3 border-t border-gray-100 flex gap-2">
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Votre question..."
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
          className="text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50"
          style={{ background: C.sarcelle }}
        >
          →
        </button>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────
function JobSearch() {
  const [keywords, setKeywords] = useState('')
  const [region, setRegion] = useState('11')
  const [regions, setRegions] = useState([])
  const [offers, setOffers] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [isScoring, setIsScoring] = useState(false)
  const [analyses, setAnalyses] = useState({})
  const [analyzingId, setAnalyzingId] = useState(null)
  const [showCvPreview, setShowCvPreview] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/jobs/regions')
      .then((r) => r.json()).then(setRegions)
    fetch('http://localhost:8000/jobs/suggest-params')
      .then((r) => r.json())
      .then((d) => { if (d.keywords) setKeywords(d.keywords); if (d.region) setRegion(d.region) })
      .catch(() => {})
  }, [])

  async function handleSearch(e) {
    e.preventDefault()
    setIsSearching(true)
    setOffers([])
    setAnalyses({})
    setError(null)
    try {
      const res = await fetch('http://localhost:8000/jobs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, region }),
      })
      const data = await res.json()
      const raw = data.offers ?? []
      if (raw.length === 0) { setError('Aucune offre trouvée.'); return }
      setOffers(raw)
      setIsScoring(true)
      const scoreRes = await fetch('http://localhost:8000/jobs/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ offers: raw }),
      })
      const scored = await scoreRes.json()
      setOffers(scored.scored_offers ?? raw)
    } catch {
      setError('Erreur lors de la recherche.')
    } finally {
      setIsSearching(false)
      setIsScoring(false)
    }
  }

  async function handleAnalyze(offerId) {
    if (analyses[offerId]) return
    setAnalyzingId(offerId)
    try {
      const res = await fetch('http://localhost:8000/jobs/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ offer_id: offerId }),
      })
      const data = await res.json()
      setAnalyses((prev) => ({ ...prev, [offerId]: data.analysis }))
    } catch {
      setAnalyses((prev) => ({ ...prev, [offerId]: "Erreur lors de l'analyse." }))
    } finally {
      setAnalyzingId(null)
    }
  }

  const maxScore = offers.length > 0 ? Math.max(...offers.map((o) => o.score ?? 0)) : 1

  return (
    <div className="flex flex-col h-full" style={{ background: C.creme }}>
      {showCvPreview && <CVPreview onClose={() => setShowCvPreview(false)} />}

      <TopBar
        keywords={keywords} setKeywords={setKeywords}
        region={region} setRegion={setRegion}
        regions={regions}
        isSearching={isSearching}
        onSearch={handleSearch}
        onShowCV={() => setShowCvPreview(true)}
      />

      <div className="flex flex-1 min-h-0">

        {/* Main: offer cards */}
        <div className="flex-1 h-full overflow-y-auto px-6 py-5">
          {isSearching && (
            <p className="text-sm text-center text-gray-400 mt-12">Recherche en cours...</p>
          )}
          {isScoring && !isSearching && (
            <p className="text-xs text-center mb-3" style={{ color: C.sarcelle }}>
              Classement par pertinence...
            </p>
          )}
          {error && (
            <p className="text-sm text-center mt-12" style={{ color: C.ecartFort }}>{error}</p>
          )}
          {!isSearching && offers.length === 0 && !error && (
            <div className="flex items-center justify-center h-full text-gray-300 text-sm select-none">
              Lancez une recherche pour afficher les offres
            </div>
          )}
          <div className="space-y-4 max-w-2xl mx-auto">
            {offers.map((offer) => {
              const ratio = maxScore > 0 ? (offer.score ?? 0) / maxScore : 0
              return (
                <OfferCard
                  key={offer.id}
                  offer={offer}
                  ratio={ratio}
                  onAnalyze={() => handleAnalyze(offer.id)}
                  isAnalyzing={analyzingId === offer.id}
                  analysis={analyses[offer.id]}
                />
              )
            })}
          </div>
        </div>

        {/* Right: chat */}
        <ChatColumn />
      </div>
    </div>
  )
}

export default JobSearch
