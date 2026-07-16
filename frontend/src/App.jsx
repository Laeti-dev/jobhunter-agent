import { useState } from 'react'
import Welcome from './components/Welcome'
import Chat from './components/Chat'
import CVImport from './components/CVImport'
import CVPanel from './components/CVPanel'
import CVPreview from './components/CVPreview'
import JobSearch from './components/JobSearch'

function App() {
  const [screen, setScreen] = useState('welcome')
  const [showCvPreview, setShowCvPreview] = useState(false)

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">

      {screen !== 'welcome' && (
        <button
          onClick={() => setScreen('welcome')}
          className="self-start mb-4 text-sm text-gray-500 hover:text-gray-700"
        >
          ← Accueil
        </button>
      )}

      {screen === 'welcome' && (
        <Welcome
          onStart={() => setScreen('job_search')}
          onImport={() => setScreen('cv_import')}
          onBuild={() => setScreen('cv_builder')}
        />
      )}

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

      {screen === 'job_search' && (
        <div className="w-full flex flex-col items-center gap-4">
          <CVPanel onShowPreview={() => setShowCvPreview(true)} />
          <JobSearch />
        </div>
      )}

      {showCvPreview && <CVPreview onClose={() => setShowCvPreview(false)} />}
    </div>
  )
}

export default App
