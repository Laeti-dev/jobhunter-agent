import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import JobMap from './JobMap'

function JobSearch() {
  const [keywords, setKeywords] = useState('')
  const [region, setRegion] = useState('11')
  const [regions, setRegions] = useState([])
  const [offers, setOffers] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [view, setView] = useState('list')
  const [expandedId, setExpandedId] = useState(null)
  const [offerDetails, setOfferDetails] = useState({})
  const [analyses, setAnalyses] = useState({})
  const [analyzingId, setAnalyzingId] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/jobs/regions')
      .then((r) => r.json())
      .then(setRegions)

    fetch('http://localhost:8000/jobs/suggest-params')
      .then((r) => r.json())
      .then((data) => {
        if (data.keywords) setKeywords(data.keywords)
        if (data.region) setRegion(data.region)
      })
      .catch(() => {})
  }, [])

  async function handleSearch(event) {
    event.preventDefault()
    setIsSearching(true)
    setOffers([])
    setAnalyses({})
    setExpandedId(null)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/jobs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keywords, region }),
      })
      const data = await response.json()
      setOffers(data.offers ?? [])
      if ((data.offers ?? []).length === 0) {
        setError('Aucune offre trouvée. Essayez des mots-clés plus simples.')
      }
    } catch {
      setError('Erreur lors de la recherche.')
    } finally {
      setIsSearching(false)
    }
  }

  async function toggleDetail(offerId) {
    if (expandedId === offerId) {
      setExpandedId(null)
      return
    }
    setExpandedId(offerId)
    if (!offerDetails[offerId]) {
      const response = await fetch(`http://localhost:8000/jobs/${offerId}`)
      const data = await response.json()
      setOfferDetails((prev) => ({ ...prev, [offerId]: data }))
    }
  }

  async function handleAnalyze(offerId) {
    if (analyses[offerId]) return
    setAnalyzingId(offerId)
    try {
      const response = await fetch('http://localhost:8000/jobs/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ offer_id: offerId }),
      })
      const data = await response.json()
      setAnalyses((prev) => ({ ...prev, [offerId]: data.analysis }))
    } catch {
      setAnalyses((prev) => ({ ...prev, [offerId]: 'Erreur lors de l\'analyse.' }))
    } finally {
      setAnalyzingId(null)
    }
  }

  const isMapView = view === 'map' && offers.length > 0

  const offerList = (compact = false) => offers.map((offer) => (
    <div key={offer.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
      <button
        onClick={() => toggleDetail(offer.id)}
        className="w-full p-4 text-left flex justify-between items-center hover:bg-gray-50 transition-colors"
      >
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm truncate">{offer.intitule}</h3>
          <p className="text-xs text-gray-500 mt-0.5 truncate">
            {offer.entreprise?.nom ?? 'Entreprise non précisée'}
            {offer.lieuTravail?.libelle ? ` · ${offer.lieuTravail.libelle}` : ''}
          </p>
        </div>
        <span className="text-gray-400 text-sm ml-2 shrink-0">
          {expandedId === offer.id ? '▲' : '▼'}
        </span>
      </button>

      {expandedId === offer.id && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100">
          {!offerDetails[offer.id] ? (
            <p className="text-xs text-gray-400 pt-3">Chargement...</p>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 pt-3 text-xs text-gray-500">
                {offerDetails[offer.id].typeContrat && <span className="bg-gray-100 px-2 py-1 rounded">{offerDetails[offer.id].typeContratLibelle ?? offerDetails[offer.id].typeContrat}</span>}
                {offerDetails[offer.id].salaire?.libelle && <span className="bg-gray-100 px-2 py-1 rounded">{offerDetails[offer.id].salaire.libelle}</span>}
                {offerDetails[offer.id].experienceLibelle && <span className="bg-gray-100 px-2 py-1 rounded">{offerDetails[offer.id].experienceLibelle}</span>}
              </div>
              <p className="text-xs text-gray-600 whitespace-pre-line">
                {offerDetails[offer.id].description?.slice(0, compact ? 300 : 600)}
                {offerDetails[offer.id].description?.length > (compact ? 300 : 600) ? '...' : ''}
              </p>
              {!analyses[offer.id] ? (
                <button
                  onClick={() => handleAnalyze(offer.id)}
                  disabled={analyzingId === offer.id}
                  className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-xl text-xs font-medium disabled:opacity-50"
                >
                  {analyzingId === offer.id ? 'Analyse en cours...' : 'Analyser avec mon CV'}
                </button>
              ) : (
                <div className="border-t border-gray-100 pt-3 prose prose-sm text-gray-700">
                  <ReactMarkdown>{analyses[offer.id]}</ReactMarkdown>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  ))

  return (
    <div className={`w-full space-y-4 ${isMapView ? 'max-w-6xl' : 'max-w-2xl'}`}>
      <form onSubmit={handleSearch} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Poste recherché</label>
            <input
              type="text"
              className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="ex: Data Scientist"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Région</label>
            <select
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              {regions.map((r) => (
                <option key={r.code} value={r.code}>{r.libelle}</option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="submit"
          disabled={isSearching || !keywords}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-xl text-sm font-medium disabled:opacity-50"
        >
          {isSearching ? 'Recherche en cours...' : 'Rechercher'}
        </button>
      </form>

      {error && <p className="text-center text-sm text-red-500">{error}</p>}

      {offers.length > 0 && (
        <div className="flex gap-2">
          <button
            onClick={() => setView('list')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium ${view === 'list' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600'}`}
          >
            Liste
          </button>
          <button
            onClick={() => setView('map')}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium ${view === 'map' ? 'bg-blue-500 text-white' : 'bg-white text-gray-600'}`}
          >
            Carte
          </button>
        </div>
      )}

      {isMapView ? (
        <div className="flex gap-4 h-[600px]">
          <div className="w-80 shrink-0 overflow-y-auto space-y-3 pr-1">
            {offerList(true)}
          </div>
          <div className="flex-1">
            <JobMap
              offers={offers}
              onSelectOffer={(id) => {
                toggleDetail(id)
              }}
            />
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {offerList(false)}
        </div>
      )}
    </div>
  )
}

export default JobSearch
