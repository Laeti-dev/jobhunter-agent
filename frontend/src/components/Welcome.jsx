import { useEffect, useState } from 'react'

function Welcome({ onStart, onImport, onBuild }) {
  const [existingCv, setExistingCv] = useState(undefined)

  useEffect(() => {
    fetch('http://localhost:8000/cv/latest')
      .then((r) => r.json())
      .then((data) => setExistingCv(data.cv ?? null))
      .catch(() => setExistingCv(null))
  }, [])

  if (existingCv === undefined) {
    return <p className="text-sm text-gray-400 text-center">Chargement...</p>
  }

  return (
    <div className="w-full max-w-md space-y-4">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">JobHunter Agent</h1>
        <p className="text-sm text-gray-500 mt-1">Votre assistant recherche d'emploi</p>
      </div>

      {existingCv && (
        <button
          onClick={onStart}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white p-4 rounded-2xl text-left transition-colors"
        >
          <p className="font-semibold text-sm">Continuer avec mon CV</p>
          <p className="text-xs text-blue-100 mt-0.5">
            {existingCv.name} · {existingCv.target_role}
          </p>
        </button>
      )}

      <button
        onClick={onImport}
        className="w-full bg-white hover:bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-2xl text-left transition-colors"
      >
        <p className="font-semibold text-sm">Importer un CV (PDF)</p>
        <p className="text-xs text-gray-500 mt-0.5">
          Uploadez votre CV existant, il sera analysé automatiquement
        </p>
      </button>

      <button
        onClick={onBuild}
        className="w-full bg-white hover:bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-2xl text-left transition-colors"
      >
        <p className="font-semibold text-sm">Créer un nouveau CV</p>
        <p className="text-xs text-gray-500 mt-0.5">
          L'agent vous pose des questions pour construire votre profil
        </p>
      </button>
    </div>
  )
}

export default Welcome
