import { useState } from 'react'
import Chat from './components/Chat'
import CVImport from './components/CVImport'
import CVPreview from './components/CVPreview'
import JobSearch from './components/JobSearch'

function App() {
  const [screen, setScreen] = useState('job_search')
  const [showCvPreview, setShowCvPreview] = useState(false)

  if (screen === 'job_search') {
    return (
      <div className="h-screen bg-gray-100 overflow-hidden">
        <JobSearch onNavigate={setScreen} />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">

      <button
        onClick={() => setScreen('job_search')}
        className="self-start mb-4 text-sm text-gray-500 hover:text-gray-700"
      >
        ← Retour
      </button>

      {screen === 'cv_builder' && (
        <div className="w-full max-w-2xl">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Créer mon CV</h2>
          <Chat
            key="cv_builder"
            endpoint="/cv/chat"
            placeholder="Répondez à l'agent..."
            stateful
            onCvReady={() => {
              setShowCvPreview(true)
              setScreen('job_search')
            }}
          />
        </div>
      )}

      {screen === 'cv_import' && (
        <CVImport onSuccess={() => setScreen('job_search')} />
      )}

      {showCvPreview && <CVPreview onClose={() => setShowCvPreview(false)} />}
    </div>
  )
}

export default App
