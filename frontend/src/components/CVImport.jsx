import { useState } from 'react'

function CVImport({ onSuccess }) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleUpload(event) {
    const file = event.target.files[0]
    if (!file) return

    setIsLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/cv/import', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail ?? 'Erreur lors de l\'import.')
      }

      onSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-md space-y-4">
      <h2 className="text-lg font-bold text-gray-800">Importer mon CV</h2>

      <div className="bg-white rounded-2xl border-2 border-dashed border-gray-300 p-8 text-center">
        {isLoading ? (
          <p className="text-sm text-gray-500">Analyse du CV en cours...</p>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-4">
              Sélectionnez votre CV au format PDF
            </p>
            <label className="cursor-pointer bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium">
              Choisir un fichier
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={handleUpload}
              />
            </label>
          </>
        )}
      </div>

      {error && <p className="text-sm text-red-500 text-center">{error}</p>}
    </div>
  )
}

export default CVImport
