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
  onSelectLocation: (location: { name: string; latitude: number; longitude: number; address?: string; region?: string }) => void;
  initialCity?: string;
}

// Center of India roughly
const DEFAULT_CENTER: [number, number] = [20.5937, 78.9629];
const DEFAULT_ZOOM = 4;

const LocationMarker = ({ position, setPosition, resolvePosition }: any) => {
  const map = useMapEvents({
    click(e) {
      setPosition(e.latlng);
      resolvePosition(e.latlng.lat, e.latlng.lng);
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

const fetchCityFromCoords = async (lat: number, lon: number, setCityName: any, setLoadingCity: any, setAddressName: any, isCurrent: () => boolean) => {
  setLoadingCity(true);
  try {
    const response = await axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`);
    if (!isCurrent()) return;
    const address = response.data.address;
    setAddressName(response.data.display_name || '');
    const city = address.city || address.town || address.village || address.state_district || address.county;
    if (city) {
      setCityName(city);
    } else {
      setCityName('Unknown Location');
    }
  } catch (error) {
    if (isCurrent()) {
      console.error("Error reverse geocoding:", error);
      setCityName('Error resolving location');
    }
  } finally {
    if (isCurrent()) setLoadingCity(false);
  }
};


export const LocationPickerModal: React.FC<LocationPickerModalProps> = ({ isOpen, onClose, onSelectLocation, initialCity }) => {
  const [position, setPosition] = useState<L.LatLng | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [cityName, setCityName] = useState(initialCity || '');
  const [addressName, setAddressName] = useState('');
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingCity, setLoadingCity] = useState(false);
  const lookupId = useRef(0);

  const resolvePosition = (lat: number, lon: number, requestId = ++lookupId.current) =>
    fetchCityFromCoords(lat, lon, setCityName, setLoadingCity, setAddressName, () => lookupId.current === requestId);

  useEffect(() => {
     if (isOpen && initialCity) {
        setSearchQuery(initialCity);
        handleSearch(null, initialCity);
     }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      lookupId.current += 1;
      setPosition(null);
      setCityName('');
      setAddressName('');
      setLoadingCity(false);
      setLoadingSearch(false);
    }
  }, [isOpen]);


  if (!isOpen) return null;

  const handleSearch = async (e: React.FormEvent | null, queryOverride?: string) => {
    if (e) e.preventDefault();
    const query = queryOverride || searchQuery;
    if (!query.trim()) return;

    const requestId = ++lookupId.current;
    setCityName('');
    setAddressName('');
    setLoadingSearch(true);
    try {
      const response = await axios.get(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      if (lookupId.current !== requestId) return;
      if (response.data && response.data.length > 0) {
        const result = response.data[0];
        const newPos = new L.LatLng(parseFloat(result.lat), parseFloat(result.lon));
        setPosition(newPos);
        setAddressName(result.display_name || '');
        await resolvePosition(newPos.lat, newPos.lng, requestId);
      } else {
         // handle not found
      }
    } catch (error) {
      if (lookupId.current === requestId) console.error("Error searching location:", error);
    } finally {
      if (lookupId.current === requestId) setLoadingSearch(false);
    }
  };

  const handleConfirm = () => {
    if (position && cityName && cityName !== 'Unknown Location' && cityName !== 'Error resolving location') {
      onSelectLocation({ name: cityName, latitude: position.lat, longitude: position.lng, address: addressName || cityName, region: addressName || undefined });
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-paper-900/60 backdrop-blur-sm">
      <div className="bg-paper-50 dark:bg-paper-800 rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden flex flex-col h-[80vh] max-h-[800px]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-paper-200 dark:border-paper-700 bg-paper-50 dark:bg-paper-900/50">
          <div className="flex items-center gap-2 text-paper-800 dark:text-white">
            <div className="p-1.5 bg-marigold-100 dark:bg-marigold-900/40 text-marigold-600 rounded-lg">
              <MapPin size={18} />
            </div>
            <h2 className="font-bold text-lg">Select a location</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-paper-400 hover:text-paper-600 dark:hover:text-paper-200 rounded-xl hover:bg-paper-200 dark:hover:bg-paper-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex flex-col gap-4 flex-1 overflow-hidden">
          
          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 text-paper-400" size={16} />
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a city..."
                className="w-full bg-paper-100 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:border-marigold-500 text-paper-900 dark:text-white"
              />
            </div>
            <button 
              type="submit"
              disabled={loadingSearch}
              className="bg-paper-900 hover:bg-paper-800 dark:bg-paper-700 dark:hover:bg-paper-600 text-white px-4 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50 flex items-center gap-2"
            >
              {loadingSearch ? <Loader size={16} className="animate-spin" /> : 'Search'}
            </button>
          </form>

          {/* Map */}
          <div className="flex-1 rounded-xl overflow-hidden border border-paper-200 dark:border-paper-700 relative z-0">
             <MapContainer center={DEFAULT_CENTER} zoom={DEFAULT_ZOOM} scrollWheelZoom={true} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <LocationMarker 
                    position={position} 
                    setPosition={setPosition} 
                    resolvePosition={resolvePosition}
                />
             </MapContainer>
          </div>

          {/* Result Footer */}
          <div className="flex items-center justify-between p-3 bg-paper-50 dark:bg-paper-900 border border-paper-200 dark:border-paper-700 rounded-xl">
             <div className="flex flex-col">
                <span className="text-[10px] text-paper-400 font-bold uppercase tracking-wider">Selected City</span>
                <div className="flex items-center gap-2">
                    {loadingCity ? (
                        <Loader size={14} className="animate-spin text-marigold-500" />
                    ) : (
                        <span className="text-sm font-bold text-paper-800 dark:text-white">
                            {cityName || 'Click on map to select'}
                        </span>
                    )}
                </div>
             </div>
             
             <button
               onClick={handleConfirm}
               disabled={!position || !cityName || cityName === 'Unknown Location' || cityName === 'Error resolving location' || loadingCity || loadingSearch}
               className="bg-marigold-600 hover:bg-marigold-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-marigold-600/20"
             >
               Confirm Location
             </button>
          </div>

        </div>
      </div>
    </div>
  );
};



