import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, MapPin, X, Loader } from 'lucide-react';
import axios from 'axios';

// Fix for default marker icon in react-leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface LocationPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectLocation: (city: string) => void;
  initialCity?: string;
}

// Center of India roughly
const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629];
const DEFAULT_ZOOM = 4;

const LocationMarker = ({ position, setPosition, setCityName, setLoadingCity }: any) => {
  const map = useMapEvents({
    click(e) {
      setPosition(e.latlng);
      fetchCityFromCoords(e.latlng.lat, e.latlng.lng, setCityName, setLoadingCity);
    },
  });

  useEffect(() => {
    if (position) {
      map.flyTo(position, map.getZoom());
    }
  }, [position, map]);

  return position === null ? null : (
    <Marker position={position} />
  );
};

const fetchCityFromCoords = async (lat: number, lon: number, setCityName: any, setLoadingCity: any) => {
  setLoadingCity(true);
  try {
    const response = await axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`);
    const address = response.data.address;
    const city = address.city || address.town || address.village || address.state_district || address.county;
    if (city) {
      setCityName(city);
    } else {
      setCityName('Unknown Location');
    }
  } catch (error) {
    console.error("Error reverse geocoding:", error);
    setCityName('Error resolving location');
  } finally {
    setLoadingCity(false);
  }
};


export const LocationPickerModal: React.FC<LocationPickerModalProps> = ({ isOpen, onClose, onSelectLocation, initialCity }) => {
  const [position, setPosition] = useState<L.LatLng | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [cityName, setCityName] = useState(initialCity || '');
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingCity, setLoadingCity] = useState(false);

  useEffect(() => {
     if (isOpen && initialCity && !position) {
        setSearchQuery(initialCity);
        handleSearch(null, initialCity);
     }
  }, [isOpen]);


  if (!isOpen) return null;

  const handleSearch = async (e: React.FormEvent | null, queryOverride?: string) => {
    if (e) e.preventDefault();
    const query = queryOverride || searchQuery;
    if (!query.trim()) return;

    setLoadingSearch(true);
    try {
      const response = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      if (response.data && response.data.length > 0) {
        const result = response.data[0];
        const newPos = new L.LatLng(parseFloat(result.lat), parseFloat(result.lon));
        setPosition(newPos);
        fetchCityFromCoords(newPos.lat, newPos.lng, setCityName, setLoadingCity);
      } else {
         // handle not found
      }
    } catch (error) {
      console.error("Error searching location:", error);
    } finally {
      setLoadingSearch(false);
    }
  };

  const handleConfirm = () => {
    if (cityName && cityName !== 'Unknown Location' && cityName !== 'Error resolving location') {
      onSelectLocation(cityName);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden flex flex-col h-[80vh] max-h-[800px]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center gap-2 text-slate-800 dark:text-white">
            <div className="p-1.5 bg-violet-100 dark:bg-violet-900/40 text-violet-600 rounded-lg">
              <MapPin size={18} />
            </div>
            <h2 className="font-bold text-lg">Select Starting Location</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex flex-col gap-4 flex-1 overflow-hidden">
          
          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 text-slate-400" size={16} />
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a city..."
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-violet-500 text-slate-900 dark:text-white"
              />
            </div>
            <button 
              type="submit"
              disabled={loadingSearch}
              className="bg-slate-900 hover:bg-slate-800 dark:bg-slate-700 dark:hover:bg-slate-600 text-white px-4 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loadingSearch ? <Loader size={16} className="animate-spin" /> : 'Search'}
            </button>
          </form>

          {/* Map */}
          <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 relative z-0">
             <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <LocationMarker 
                    position={position} 
                    setPosition={setPosition} 
                    setCityName={setCityName}
                    setLoadingCity={setLoadingCity}
                />
             </MapContainer>
          </div>

          {/* Result Footer */}
          <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl">
             <div className="flex flex-col">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Selected City</span>
                <div className="flex items-center gap-2">
                    {loadingCity ? (
                        <Loader size={14} className="animate-spin text-violet-500" />
                    ) : (
                        <span className="text-sm font-bold text-slate-800 dark:text-white">
                            {cityName || 'Click on map to select'}
                        </span>
                    )}
                </div>
             </div>
             
             <button
               onClick={handleConfirm}
               disabled={!cityName || cityName === 'Unknown Location' || cityName === 'Error resolving location' || loadingCity}
               className="bg-violet-600 hover:bg-violet-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-violet-600/20"
             >
               Confirm Location
             </button>
          </div>

        </div>
      </div>
    </div>
  );
};
