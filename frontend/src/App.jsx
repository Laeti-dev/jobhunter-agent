import { useState } from 'react'
import Chat from './components/Chat'
import CVPreview from './components/CVPreview'
import JobSearch from './components/JobSearch'

const TABS = {
  chat: { label: "Chat", endpoint: "/chat", placeholder: "Posez votre question...", stateful: false },
  cv: { label: "CV Builder", endpoint: "/cv/chat", placeholder: "Répondez à l'agent...", stateful: true },
  jobs: { label: "Offres", endpoint: null, placeholder: null, stateful: false },
};

function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [showCvPreview, setShowCvPreview] = useState(false);
  const tab = TABS[activeTab];

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4 gap-4">
      <div className="w-full max-w-2xl">
        <h1 className="text-xl font-bold text-gray-800">JobHunter Agent</h1>
        <p className="text-sm text-gray-500 mb-4">Votre assistant recherche d'emploi</p>

        <div className="flex gap-2 mb-2">
          {Object.entries(TABS).map(([key, value]) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeTab === key ? "bg-blue-500 text-white" : "bg-white text-gray-600"
              }`}
            >
              {value.label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === 'jobs' ? (
        <JobSearch />
      ) : (
        <Chat
          key={tab.endpoint}
          endpoint={tab.endpoint}
          placeholder={tab.placeholder}
          stateful={tab.stateful}
          onCvReady={() => setShowCvPreview(true)}
        />
      )}

      {showCvPreview && <CVPreview onClose={() => setShowCvPreview(false)} />}
    </div>
  );
}

export default App;
