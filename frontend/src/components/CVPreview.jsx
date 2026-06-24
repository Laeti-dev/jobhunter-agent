import { useEffect, useState } from 'react'

function CVPreview({ onClose }) {
  const [cv, setCv] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/cv/latest')
      .then((response) => response.json())
      .then((data) => setCv(data.cv))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl shadow-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-gray-800">Ton CV</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {isLoading && <p className="text-gray-400">Chargement...</p>}
        {!isLoading && !cv && <p className="text-gray-400">Aucun CV trouvé.</p>}

        {cv && (
          <div className="space-y-4 text-sm text-gray-700">
            <div>
              <h3 className="font-semibold text-gray-900 text-base">{cv.name}</h3>
              <p>{[cv.email, cv.phone, cv.city].filter(Boolean).join(' · ')}</p>
              {cv.target_role && <p className="text-blue-600">{cv.target_role}</p>}
            </div>

            {cv.summary && <p>{cv.summary}</p>}

            {cv.experiences?.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Expériences</h4>
                {cv.experiences.map((experience, index) => (
                  <div key={index} className="mb-2">
                    <p className="font-medium">{experience.title} — {experience.company}</p>
                    <p className="text-gray-500 text-xs">
                      {experience.start_date} → {experience.end_date || "présent"}
                    </p>
                    <ul className="list-disc list-inside">
                      {experience.achievements?.map((achievement, i) => (
                        <li key={i}>{achievement}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}

            {cv.education?.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Formation</h4>
                {cv.education.map((education, index) => (
                  <div key={index} className="mb-2">
                    <p className="font-medium">{education.degree} — {education.institution}</p>
                    <p className="text-gray-500 text-xs">{education.field_of_study}</p>
                  </div>
                ))}
              </div>
            )}

            {cv.tech_skills?.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Compétences techniques</h4>
                <p>{cv.tech_skills.join(', ')}</p>
              </div>
            )}

            {cv.soft_skills?.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Soft skills</h4>
                <p>{cv.soft_skills.join(', ')}</p>
              </div>
            )}

            {cv.spoken_languages?.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-1">Langues</h4>
                <p>{cv.spoken_languages.join(', ')}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default CVPreview;
