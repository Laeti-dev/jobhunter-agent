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
  const [showDetail, setShowDetail] = useState(false)
  const [detail, setDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  async function handleToggleDetail() {
    if (showDetail) { setShowDetail(false); return }
    setShowDetail(true)
    if (detail) return  // already fetched
    setLoadingDetail(true)
    try {
      const res = await fetch(`http://localhost:8000/jobs/${offer.id}/enrich`)
      const data = await res.json()
      setDetail(data)
    } catch {
      setDetail({ summary: ["Erreur lors du chargement du détail."], matched_skills: [], missing_skills: [], description: "" })
    } finally {
      setLoadingDetail(false)
    }
  }

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

      {/* Skill tags — matched always visible, missing appear after detail fetch */}
      {(() => {
        const matched = detail?.matched_skills ?? offer.matched_skills ?? []
        const missing = detail?.missing_skills ?? []
        if (matched.length === 0 && missing.length === 0) return null
        return (
          <div className="flex flex-wrap gap-1.5">
            {matched.map((skill) => (
              <span key={skill} className="text-xs px-2.5 py-1 rounded-full font-medium tracking-wide"
                style={{ background: `${C.pointFort}1A`, color: C.pointFort }}>
                {skill}
              </span>
            ))}
            {missing.map((skill) => (
              <span key={skill} className="text-xs px-2.5 py-1 rounded-full font-medium tracking-wide"
                style={{ background: `${C.ecartFort}1A`, color: C.ecartFort }}>
                {skill}
              </span>
            ))}
          </div>
        )
      })()}

      {/* Detail toggle */}
      <button
        onClick={handleToggleDetail}
        className="text-xs text-gray-400 hover:text-gray-600 transition-colors text-left"
      >
        {showDetail ? '▲ Masquer le détail' : '▼ Voir le détail'}
      </button>

      {/* Detail panel */}
      {showDetail && (
        <div className="rounded-xl p-3 space-y-3 text-xs" style={{ background: C.creme }}>
          {loadingDetail ? (
            <p style={{ color: C.sarcelle }}>Chargement...</p>
          ) : detail ? (
            <>
              <ul className="space-y-1 list-none">
                {detail.summary.map((bullet, i) => (
                  <li key={i} className="flex gap-2" style={{ color: C.ardoise }}>
                    <span style={{ color: C.sarcelle }}>•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
              {detail.description && (
                <details>
                  <summary className="cursor-pointer text-gray-400 hover:text-gray-600">
                    Description complète
                  </summary>
                  <p className="mt-2 whitespace-pre-wrap leading-relaxed" style={{ color: C.ardoise }}>
                    {detail.description}
                  </p>
                </details>
              )}
            </>
          ) : null}
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
function ChatColumn({ onNavigate, onSearch }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showCvActions, setShowCvActions] = useState(false)
  const [showSearchConfirm, setShowSearchConfirm] = useState(false)
  const [suggestedRole, setSuggestedRole] = useState('')
  const [showRolePicker, setShowRolePicker] = useState(false)
  const [alternativeRoles, setAlternativeRoles] = useState([])
  const [loadingRoles, setLoadingRoles] = useState(false)
  const [awaitingCustomRole, setAwaitingCustomRole] = useState(false)
  const [uploadingCv, setUploadingCv] = useState(false)
  const bottomRef = useRef(null)
  const fileRef = useRef(null)

  useEffect(() => {
    fetch('http://localhost:8000/cv/latest')
      .then((r) => r.json())
      .then((data) => {
        if (data.cv) {
          const firstName = data.cv.name?.split(' ')[0] ?? 'vous'
          const role = data.cv.target_role ?? ''
          setSuggestedRole(role)
          setMessages([
            {
              role: 'assistant',
              content: `Bonjour **${firstName}** ! Votre CV est chargé.\n\nJe vous propose de rechercher des offres pour le poste **${role || 'de votre choix'}**. C'est bien ça ?`,
            },
          ])
          setShowSearchConfirm(true)
        } else {
          setMessages([{
            role: 'assistant',
            content: `Bonjour ! Pour commencer, j'ai besoin de votre CV.\n\nVous pouvez charger un PDF existant, ou créer votre CV avec moi étape par étape.`,
          }])
          setShowCvActions(true)
        }
      })
      .catch(() => {
        setMessages([{ role: 'assistant', content: 'Bonjour ! Comment puis-je vous aider ?' }])
      })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, showCvActions, showSearchConfirm, showRolePicker, loadingRoles])

  function confirmSearch(role) {
    setShowSearchConfirm(false)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: `Oui, rechercher "${role}"` },
      { role: 'assistant', content: `Lancement de la recherche pour **${role}**...` },
    ])
    onSearch?.(role)
  }

  async function requestCustomRole() {
    setShowSearchConfirm(false)
    setLoadingRoles(true)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: 'Je cherche un autre poste' },
    ])
    try {
      const res = await fetch(`http://localhost:8000/jobs/suggest-roles?role=${encodeURIComponent(suggestedRole)}`)
      const data = await res.json()
      setAlternativeRoles(data.roles ?? [])
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Voici 3 postes qui correspondent à votre profil :' },
      ])
      setShowRolePicker(true)
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Quel poste recherchez-vous ?' },
      ])
      setAwaitingCustomRole(true)
    } finally {
      setLoadingRoles(false)
    }
  }

  function pickRole(role) {
    setShowRolePicker(false)
    setSuggestedRole(role)
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: role },
      { role: 'assistant', content: `Lancement de la recherche pour **${role}**...` },
    ])
    onSearch?.(role)
  }

  function openFreeInput() {
    setShowRolePicker(false)
    setAwaitingCustomRole(true)
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: 'Quel poste recherchez-vous ?' },
    ])
  }

  async function handleCvUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploadingCv(true)
    setShowCvActions(false)
    setMessages((prev) => [...prev, { role: 'user', content: `📎 ${file.name}` }])
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('http://localhost:8000/cv/import', { method: 'POST', body: form })
      const data = await res.json()
      const name = data.cv?.name?.split(' ')[0] ?? 'vous'
      const role = data.cv?.target_role ?? ''
      setSuggestedRole(role)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `CV importé ! Bonjour **${name}**.\n\nJe vous propose de rechercher **${role || 'un poste'}**. C'est bien ça ?`,
      }])
      setShowSearchConfirm(true)
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: "Erreur lors de l'import. Vérifiez que le fichier est bien un PDF." }])
      setShowCvActions(true)
    } finally {
      setUploadingCv(false)
      e.target.value = ''
    }
  }

  async function sendMessage() {
    if (!input.trim() || isLoading) return
    const text = input.trim()
    setInput('')

    // Intercept: user is providing a custom role
    if (awaitingCustomRole) {
      setAwaitingCustomRole(false)
      setSuggestedRole(text)
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: text },
        { role: 'assistant', content: `Lancement de la recherche pour **${text}**...` },
      ])
      onSearch?.(text)
      return
    }

    const userMsg = { role: 'user', content: text }
    const updated = [...messages, userMsg]
    setMessages(updated)
    setIsLoading(true)
    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history: messages }),
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
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[85%] px-3 py-2 rounded-xl text-xs prose prose-xs"
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

        {/* Search confirmation buttons */}
        {showSearchConfirm && (
          <div className="flex flex-col gap-2 pl-1 pt-1">
            <button
              onClick={() => confirmSearch(suggestedRole)}
              className="text-left text-xs font-medium px-3 py-2 rounded-lg text-white transition-opacity hover:opacity-90"
              style={{ background: C.sarcelle }}
            >
              ✓ Oui, lancer la recherche
            </button>
            <button
              onClick={requestCustomRole}
              className="text-left text-xs font-medium px-3 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
            >
              ✏️ Non, autre poste
            </button>
          </div>
        )}

        {/* Loading spinner while fetching role suggestions */}
        {loadingRoles && (
          <div className="flex justify-start pl-1 pt-1">
            <span className="text-xs" style={{ color: C.sarcelle }}>Analyse du profil...</span>
          </div>
        )}

        {/* Alternative role picker */}
        {showRolePicker && (
          <div className="flex flex-col gap-2 pl-1 pt-1">
            {alternativeRoles.map((role) => (
              <button
                key={role}
                onClick={() => pickRole(role)}
                className="text-left text-xs font-medium px-3 py-2 rounded-lg border transition-colors hover:opacity-90"
                style={{ borderColor: C.sarcelle, color: C.sarcelle }}
              >
                {role}
              </button>
            ))}
            <button
              onClick={openFreeInput}
              className="text-left text-xs font-medium px-3 py-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50"
            >
              ✏️ Autre...
            </button>
          </div>
        )}

        {/* CV action buttons */}
        {showCvActions && (
          <div className="flex flex-col gap-2 pl-1 pt-1">
            <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={handleCvUpload} />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploadingCv}
              className="text-left text-xs font-medium px-3 py-2 rounded-lg border transition-colors"
              style={{ borderColor: C.sarcelle, color: C.sarcelle }}
            >
              📎 {uploadingCv ? 'Import en cours...' : 'Charger un PDF'}
            </button>
            <button
              onClick={() => onNavigate?.('cv_builder')}
              className="text-left text-xs font-medium px-3 py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
            >
              ✏️ Créer depuis zéro
            </button>
          </div>
        )}

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
          placeholder={awaitingCustomRole ? 'Entrez le poste souhaité...' : 'Votre question...'}
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
function JobSearch({ onNavigate }) {
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

  async function runSearch(kw, reg) {
    setIsSearching(true)
    setOffers([])
    setAnalyses({})
    setError(null)
    try {
      const res = await fetch('http://localhost:8000/jobs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords: kw, region: reg }),
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

  function handleSearch(e) {
    e.preventDefault()
    runSearch(keywords, region)
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
        <ChatColumn
          onNavigate={onNavigate}
          onSearch={(kw) => { setKeywords(kw); runSearch(kw, region) }}
        />
      </div>
    </div>
  )
}

export default JobSearch
