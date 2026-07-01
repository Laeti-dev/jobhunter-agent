import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const EXPERIENCE_OPTIONS = [
  { value: '', label: 'Indifférent' },
  { value: '1', label: 'Moins d\'1 an' },
  { value: '2', label: '1 à 3 ans' },
  { value: '3', label: 'Plus de 3 ans' },
]

const EDUCATION_OPTIONS = [
  { value: '', label: 'Indifférent' },
  { value: 'NV3', label: 'BAC+2 (BTS, DUT)' },
  { value: 'NV2', label: 'BAC+3 / BAC+4 (Licence)' },
  { value: 'NV1', label: 'BAC+5 et plus (Master, Ingénieur)' },
]

const DEFAULT_PARAMS = { keywords: '', experience: '', education_level: '', region: '11' }

function JobSearch() {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [offers, setOffers] = useState([])
  const [isSuggesting, setIsSuggesting] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [analyzingId, setAnalyzingId] = useState(null)
  const [analyses, setAnalyses] = useState({})
  const [error, setError] = useState(null)

  useEffect(() => {
    setIsSuggesting(true)
    fetch('http://localhost:8000/jobs/suggest-params')
      .then((response) => response.json())
      .then((data) => {
        if (data.query) {
          setParams({
            keywords: data.query.keywords ?? '',
            experience: data.query.experience ?? '',
            education_level: data.query.education_level ?? '',
            region: data.query.region ?? '11',
          })
        }
      })
      .catch(() => setError('Aucun CV trouvé. Créez-en un via le CV Builder.'))
      .finally(() => setIsSuggesting(false))
  }, [])

  async function handleSearch(event) {
    event.preventDefault()
    setIsSearching(true)
    setOffers([])
    setAnalyses({})
    setError(null)

    const body = {
      keywords: params.keywords,
      region: params.region,
      experience: params.experience || null,
      education_level: params.education_level || null,
    }

    try {
      const response = await fetch('http://localhost:8000/jobs/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await response.json()
      setOffers(data.offers ?? [])
      if ((data.offers ?? []).length === 0) {
        setError('Aucune offre trouvée pour ces critères. Essayez des mots-clés plus simples.')
      }
    } catch {
      setError('Erreur lors de la recherche. Vérifiez que le serveur tourne.')
    } finally {
      setIsSearching(false)
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

  return (
    <div className="w-full max-w-2xl space-y-4">
      <form onSubmit={handleSearch} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mots-clés</label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={params.keywords}
            onChange={(e) => setParams({ ...params, keywords: e.target.value })}
            placeholder={isSuggesting ? 'Chargement...' : 'ex: AI Engineer Python'}
          />
        </div>

        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Expérience</label>
            <select
              className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={params.experience}
              onChange={(e) => setParams({ ...params, experience: e.target.value })}
            >
              {EXPERIENCE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Niveau de formation</label>
            <select
              className="w-full border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              value={params.education_level}
              onChange={(e) => setParams({ ...params, education_level: e.target.value })}
            >
              {EDUCATION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSearching || !params.keywords}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-xl text-sm font-medium disabled:opacity-50"
        >
          {isSearching ? 'Recherche en cours...' : 'Rechercher'}
        </button>
      </form>

      {error && <p className="text-center text-sm text-red-500">{error}</p>}

      {offers.map((offer) => (
        <div key={offer.id} className="bg-white rounded-2xl shadow-sm p-5 space-y-2">
          <div className="flex justify-between items-start gap-3">
            <div>
              <h3 className="font-semibold text-gray-900 text-sm">{offer.intitule}</h3>
              <p className="text-xs text-gray-500">
                {offer.entreprise?.nom ?? 'Entreprise non précisée'}
                {offer.lieuTravail?.libelle ? ` · ${offer.lieuTravail.libelle}` : ''}
              </p>
            </div>
            <button
              onClick={() => handleAnalyze(offer.id)}
              disabled={analyzingId === offer.id}
              className="shrink-0 bg-blue-50 hover:bg-blue-100 text-blue-600 px-3 py-1 rounded-lg text-xs font-medium disabled:opacity-50"
            >
              {analyzingId === offer.id ? 'Analyse...' : analyses[offer.id] ? 'Ré-analyser' : 'Analyser'}
            </button>
          </div>

          <p className="text-xs text-gray-600 line-clamp-2">
            {offer.description?.slice(0, 200)}...
          </p>

          {analyses[offer.id] && (
            <div className="mt-3 pt-3 border-t border-gray-100 prose prose-sm text-gray-700">
              <ReactMarkdown>{analyses[offer.id]}</ReactMarkdown>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default JobSearch
