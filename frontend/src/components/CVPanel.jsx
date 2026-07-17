import { useEffect, useState } from 'react'
import CVImport from './CVImport'
import CVPreview from './CVPreview'

function extractGithubUsername(githubField) {
  if (!githubField) return null
  // Handles "https://github.com/username", "github.com/username", or plain "username"
  const match = githubField.match(/github\.com\/([^/\s]+)/)
  return match ? match[1] : githubField
}

function CVPanel({ onNavigate }) {
  const [cv, setCv] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [indexedRepos, setIndexedRepos] = useState([])
  const [isIndexing, setIsIndexing] = useState(false)
  const [indexStatus, setIndexStatus] = useState(null)

  function fetchCV() {
    fetch('http://localhost:8000/cv/latest')
      .then((r) => r.json())
      .then((data) => { setCv(data.cv); setLoaded(true) })
      .catch(() => setLoaded(true))
  }

  useEffect(() => {
    fetchCV()
    fetch('http://localhost:8000/github/repos')
      .then((r) => r.json())
      .then((data) => setIndexedRepos(data.repos ?? []))
      .catch(() => {})
  }, [])

  if (!loaded) return null

  if (!cv) {
    return (
      <div className="bg-white rounded-2xl p-4 space-y-3">
        <p className="text-sm font-semibold text-gray-700">Mon CV</p>
        <p className="text-xs text-gray-400">Aucun CV chargé.</p>
        <CVImport onSuccess={fetchCV} compact />
        <button
          onClick={() => onNavigate?.('cv_builder')}
          className="w-full text-xs text-blue-500 hover:underline"
        >
          Créer mon CV avec l'agent →
        </button>
      </div>
    )
  }

  const githubUsername = extractGithubUsername(cv.github)

  async function handleIndexRepos() {
    if (!githubUsername) return
    setIsIndexing(true)
    setIndexStatus(null)
    try {
      const response = await fetch('http://localhost:8000/github/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: githubUsername }),
      })
      const data = await response.json()
      setIndexedRepos(data.repos ?? [])
      setIndexStatus(`${data.indexed} repos indexés`)
    } catch {
      setIndexStatus("Erreur lors de l'indexation")
    } finally {
      setIsIndexing(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 space-y-3">
      {showPreview && <CVPreview onClose={() => setShowPreview(false)} />}
      {/* CV summary */}
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold text-gray-900">{cv.name}</p>
          {cv.target_role && (
            <p className="text-sm text-blue-600">{cv.target_role}</p>
          )}
          {cv.tech_skills?.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              {cv.tech_skills.slice(0, 5).join(' · ')}
            </p>
          )}
        </div>
        <button
          onClick={() => setShowPreview(true)}
          className="text-xs text-blue-500 hover:underline shrink-0 ml-4"
        >
          Voir CV complet
        </button>
      </div>

      {/* GitHub section */}
      <div className="border-t border-gray-100 pt-3 space-y-2">
        {githubUsername ? (
          <>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">GitHub :</span>
              <a
                href={`https://github.com/${githubUsername}`}
                target="_blank"
                rel="noreferrer"
                className="text-blue-500 hover:underline font-medium"
              >
                {githubUsername}
              </a>
            </div>

            {indexedRepos.length > 0 ? (
              <div className="space-y-1.5">
                <p className="text-xs text-gray-500">
                  {indexedRepos.length} repos indexés pour la lettre de motivation
                </p>
                <div className="flex flex-wrap gap-1">
                  {indexedRepos.map((repo) => (
                    <span
                      key={repo}
                      className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600"
                    >
                      {repo}
                    </span>
                  ))}
                </div>
                <button
                  onClick={handleIndexRepos}
                  disabled={isIndexing}
                  className="text-xs text-gray-400 hover:text-gray-600 disabled:opacity-50"
                >
                  {isIndexing ? 'Mise à jour...' : '↻ Mettre à jour'}
                </button>
              </div>
            ) : (
              <button
                onClick={handleIndexRepos}
                disabled={isIndexing}
                className="bg-gray-900 hover:bg-gray-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50"
              >
                {isIndexing ? 'Indexation en cours...' : 'Indexer mes repos épinglés'}
              </button>
            )}

            {indexStatus && (
              <p className="text-xs text-green-600">{indexStatus}</p>
            )}
          </>
        ) : (
          <p className="text-xs text-gray-400">
            Aucun profil GitHub détecté dans le CV.
          </p>
        )}
      </div>
    </div>
  )
}

export default CVPanel
