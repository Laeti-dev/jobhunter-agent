import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

function JobSearch() {
  const [keywords, setKeywords] = useState('')
  const [region, setRegion] = useState('11')
  const [regions, setRegions] = useState([])
  const [offers, setOffers] = useState([])
  const [isSearching, setIsSearching] = useState(false)
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

  const detail = expandedId ? offerDetails[expandedId] : null

  return (
    <div className="w-full max-w-2xl space-y-4">
      <form onSubmit={handleSearch} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Poste recherché</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="ex: Data Scientist"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Région</label>
          <select
            className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
          >
            {regions.map((r) => (
              <option key={r.code} value={r.code}>{r.libelle}</option>
            ))}
          </select>
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

      {offers.map((offer) => (
        <div key={offer.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <button
            onClick={() => toggleDetail(offer.id)}
            className="w-full p-5 text-left flex justify-between items-center hover:bg-gray-50 transition-colors"
          >
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">{offer.intitule}</h3>
              <p className="text-xs text-gray-500 mt-0.5">
                {offer.entreprise?.nom ?? 'Entreprise non précisée'}
                {offer.lieuTravail?.libelle ? ` · ${offer.lieuTravail.libelle}` : ''}
              </p>
            </div>
            <span className="text-gray-400 text-lg ml-4">
              {expandedId === offer.id ? '▲' : '▼'}
            </span>
          </button>

          {expandedId === offer.id && (
            <div className="px-5 pb-5 space-y-4 border-t border-gray-100">
              {!detail ? (
                <p className="text-xs text-gray-400 pt-3">Chargement du détail...</p>
              ) : (
                <>
                  <div className="flex gap-3 pt-3 text-xs text-gray-500">
                    {detail.typeContrat && <span className="bg-gray-100 px-2 py-1 rounded">{detail.typeContratLibelle ?? detail.typeContrat}</span>}
                    {detail.salaire?.libelle && <span className="bg-gray-100 px-2 py-1 rounded">{detail.salaire.libelle}</span>}
                    {detail.experienceLibelle && <span className="bg-gray-100 px-2 py-1 rounded">{detail.experienceLibelle}</span>}
                  </div>

                  <p className="text-xs text-gray-600 whitespace-pre-line">
                    {detail.description?.slice(0, 600)}
                    {detail.description?.length > 600 ? '...' : ''}
                  </p>

                  {!analyses[offer.id] ? (
                    <button
                      onClick={() => handleAnalyze(offer.id)}
                      disabled={analyzingId === offer.id}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-medium disabled:opacity-50"
                    >
                      {analyzingId === offer.id ? 'Analyse RAG en cours...' : 'Analyser avec mon CV'}
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
      ))}
    </div>
  )
}

export default JobSearch
