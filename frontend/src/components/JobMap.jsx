import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Fix Leaflet marker icons broken by Vite's asset bundling
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

const IDF_CENTER = [48.8566, 2.3522]

function JobMap({ offers, onSelectOffer }) {
  const geoOffers = offers.filter(
    (o) => o.lieuTravail?.latitude && o.lieuTravail?.longitude
  )

  const center = geoOffers.length > 0
    ? [geoOffers[0].lieuTravail.latitude, geoOffers[0].lieuTravail.longitude]
    : IDF_CENTER

  return (
    <MapContainer
      center={center}
      zoom={10}
      className="h-full w-full rounded-2xl z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {geoOffers.map((offer) => (
        <Marker
          key={offer.id}
          position={[offer.lieuTravail.latitude, offer.lieuTravail.longitude]}
        >
          <Popup>
            <div className="text-sm space-y-1">
              <p className="font-semibold">{offer.intitule}</p>
              <p className="text-gray-500 text-xs">
                {offer.entreprise?.nom ?? 'Entreprise non précisée'}
              </p>
              <p className="text-gray-500 text-xs">{offer.lieuTravail.libelle}</p>
              <button
                onClick={() => onSelectOffer(offer.id)}
                className="mt-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-xs"
              >
                Voir le détail
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

export default JobMap
