"""
Enhanced seed data with international destinations and more Indian locations
"""
from sqlalchemy.orm import Session
from app.models import Destination

INTERNATIONAL_DESTINATIONS = [
    # SOUTHEAST ASIA (15 destinations)
    {
        "name": "Bali", "state": "Indonesia", "avg_travel_cost": 25000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.8, "category": "Beach",
        "best_season": "April to October", "description": "Indonesian paradise with temples, rice terraces, beaches, and vibrant culture.",
        "budget_tier": "Mid-range", "recommended_duration": 7, "comfort_level": 70,
        "beach_score": 0.9, "nature_score": 0.7, "romantic_score": 0.8, "adventure_score": 0.6,
        "attractions": ["Ubud Rice Terraces", "Tanah Lot Temple", "Seminyak Beach", "Mount Batur"]
    },
    {
        "name": "Bangkok", "state": "Thailand", "avg_travel_cost": 22000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 1000.0, "rating": 4.6, "category": "City Exploration",
        "best_season": "November to February", "description": "Vibrant capital with ornate temples, street food, markets, and nightlife.",
        "budget_tier": "Budget", "recommended_duration": 4, "comfort_level": 65,
        "city_score": 0.9, "family_score": 0.7, "adventure_score": 0.5,
        "attractions": ["Grand Palace", "Wat Pho", "Floating Markets", "Khao San Road"]
    },
    {
        "name": "Phuket", "state": "Thailand", "avg_travel_cost": 23000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1500.0, "rating": 4.7, "category": "Beach",
        "best_season": "November to April", "description": "Thailand's largest island with stunning beaches, nightlife, and water sports.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 70,
        "beach_score": 0.9, "adventure_score": 0.7, "romantic_score": 0.6,
        "attractions": ["Patong Beach", "Phi Phi Islands", "Big Buddha", "Old Phuket Town"]
    },
    {
        "name": "Siem Reap", "state": "Cambodia", "avg_travel_cost": 20000.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 800.0, "rating": 4.8, "category": "Religious",
        "best_season": "November to March", "description": "Gateway to Angkor Wat temple complex, ancient ruins, and Khmer culture.",
        "budget_tier": "Budget", "recommended_duration": 4, "comfort_level": 60,
        "religious_score": 0.9, "nature_score": 0.6, "family_score": 0.7,
        "attractions": ["Angkor Wat", "Bayon Temple", "Ta Prohm", "Angkor Thom"]
    },
    {
        "name": "Hanoi", "state": "Vietnam", "avg_travel_cost": 21000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 700.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to December", "description": "Vietnam's capital with old quarter, street food, lakes, and French colonial architecture.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 60,
        "city_score": 0.8, "family_score": 0.6, "solo_score": 0.7,
        "attractions": ["Old Quarter", "Hoan Kiem Lake", "Ha Long Bay trip", "Temple of Literature"]
    },
    {
        "name": "Da Nang", "state": "Vietnam", "avg_travel_cost": 22000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 900.0, "rating": 4.6, "category": "Beach",
        "best_season": "February to May", "description": "Coastal city with pristine beaches, Marble Mountains, and nearby ancient Hoi An.",
        "budget_tier": "Budget", "recommended_duration": 4, "comfort_level": 65,
        "beach_score": 0.8, "nature_score": 0.6, "family_score": 0.7,
        "attractions": ["My Khe Beach", "Marble Mountains", "Dragon Bridge", "Ba Na Hills"]
    },
    {
        "name": "Singapore", "state": "Singapore", "avg_travel_cost": 30000.0, "avg_hotel_cost": 6000.0,
        "avg_food_cost": 1500.0, "avg_activity_cost": 2000.0, "rating": 4.8, "category": "City Exploration",
        "best_season": "February to April", "description": "Modern city-state with futuristic architecture, diverse food, and world-class attractions.",
        "budget_tier": "Premium", "recommended_duration": 4, "comfort_level": 90,
        "city_score": 0.9, "family_score": 0.9, "solo_score": 0.7,
        "attractions": ["Marina Bay Sands", "Gardens by the Bay", "Sentosa Island", "Universal Studios"]
    },
    {
        "name": "Kuala Lumpur", "state": "Malaysia", "avg_travel_cost": 24000.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1000.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "May to July", "description": "Malaysian capital with Petronas Towers, diverse culture, street markets, and food scene.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 70,
        "city_score": 0.8, "family_score": 0.7, "solo_score": 0.6,
        "attractions": ["Petronas Towers", "Batu Caves", "Bukit Bintang", "Central Market"]
    },
    {
        "name": "Langkawi", "state": "Malaysia", "avg_travel_cost": 25000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1200.0, "rating": 4.6, "category": "Beach",
        "best_season": "November to March", "description": "Tropical archipelago with beaches, duty-free shopping, cable car, and rainforests.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 75,
        "beach_score": 0.9, "nature_score": 0.7, "romantic_score": 0.7,
        "attractions": ["Pantai Cenang", "Sky Bridge", "Island Hopping", "Underwater World"]
    },
    {
        "name": "Colombo", "state": "Sri Lanka", "avg_travel_cost": 18000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 700.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "December to March", "description": "Sri Lankan capital with colonial architecture, beaches, temples, and vibrant markets.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 65,
        "city_score": 0.7, "beach_score": 0.5, "family_score": 0.6,
        "attractions": ["Galle Face Green", "Gangaramaya Temple", "Pettah Market", "National Museum"]
    },
    {
        "name": "Ella", "state": "Sri Lanka", "avg_travel_cost": 19000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 600.0, "rating": 4.7, "category": "Nature",
        "best_season": "December to March", "description": "Hill country gem with tea plantations, Nine Arch Bridge, and stunning mountain views.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 60,
        "nature_score": 0.9, "adventure_score": 0.7, "romantic_score": 0.6,
        "attractions": ["Nine Arch Bridge", "Little Adams Peak", "Ravana Falls", "Tea Factory Tour"]
    },
    {
        "name": "Kathmandu", "state": "Nepal", "avg_travel_cost": 15000.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 600.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to December", "description": "Himalayan capital with ancient temples, stupas, palaces, and trekking gateway.",
        "budget_tier": "Budget", "recommended_duration": 4, "comfort_level": 55,
        "religious_score": 0.9, "nature_score": 0.6, "adventure_score": 0.8,
        "attractions": ["Swayambhunath", "Pashupatinath", "Boudhanath Stupa", "Durbar Square"]
    },
    {
        "name": "Pokhara", "state": "Nepal", "avg_travel_cost": 16000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 800.0, "rating": 4.6, "category": "Adventure",
        "best_season": "October to November", "description": "Lake city with Annapurna views, paragliding, trekking, and peaceful lakeside cafes.",
        "budget_tier": "Budget", "recommended_duration": 4, "comfort_level": 60,
        "adventure_score": 0.9, "nature_score": 0.8, "romantic_score": 0.5,
        "attractions": ["Phewa Lake", "Paragliding", "Peace Pagoda", "Sarangkot Sunrise"]
    },
    {
        "name": "Pattaya", "state": "Thailand", "avg_travel_cost": 23000.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1300.0, "rating": 4.3, "category": "Beach",
        "best_season": "November to February", "description": "Beach resort city with water sports, nightlife, floating markets, and temples.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "beach_score": 0.7, "city_score": 0.6, "family_score": 0.7,
        "attractions": ["Pattaya Beach", "Coral Island", "Sanctuary of Truth", "Walking Street"]
    },
    {
        "name": "Luang Prabang", "state": "Laos", "avg_travel_cost": 21000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 700.0, "rating": 4.7, "category": "Religious",
        "best_season": "November to March", "description": "UNESCO town with French colonial architecture, Buddhist temples, and Mekong River.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 60,
        "religious_score": 0.8, "nature_score": 0.7, "romantic_score": 0.6,
        "attractions": ["Kuang Si Falls", "Mount Phousi", "Night Market", "Alms Giving Ceremony"]
    },

    # MIDDLE EAST (10 destinations)
    {
        "name": "Dubai", "state": "UAE", "avg_travel_cost": 35000.0, "avg_hotel_cost": 8000.0,
        "avg_food_cost": 2000.0, "avg_activity_cost": 3000.0, "rating": 4.7, "category": "City Exploration",
        "best_season": "November to March", "description": "Futuristic city with skyscrapers, luxury shopping, desert safaris, and man-made islands.",
        "budget_tier": "Premium", "recommended_duration": 5, "comfort_level": 95,
        "city_score": 0.9, "family_score": 0.8, "beach_score": 0.6,
        "attractions": ["Burj Khalifa", "Dubai Mall", "Desert Safari", "Palm Jumeirah"]
    },
    {
        "name": "Abu Dhabi", "state": "UAE", "avg_travel_cost": 36000.0, "avg_hotel_cost": 7500.0,
        "avg_food_cost": 1800.0, "avg_activity_cost": 2500.0, "rating": 4.6, "category": "City Exploration",
        "best_season": "November to March", "description": "UAE capital with Sheikh Zayed Mosque, Ferrari World, and cultural attractions.",
        "budget_tier": "Premium", "recommended_duration": 3, "comfort_level": 95,
        "city_score": 0.8, "family_score": 0.9, "religious_score": 0.6,
        "attractions": ["Sheikh Zayed Mosque", "Louvre Abu Dhabi", "Ferrari World", "Corniche Beach"]
    },
    {
        "name": "Istanbul", "state": "Turkey", "avg_travel_cost": 28000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 1200.0, "rating": 4.8, "category": "City Exploration",
        "best_season": "April to May, September to November", "description": "Historic city bridging Europe and Asia with palaces, mosques, bazaars, and Bosphorus.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 70,
        "city_score": 0.9, "religious_score": 0.7, "family_score": 0.7,
        "attractions": ["Hagia Sophia", "Blue Mosque", "Grand Bazaar", "Topkapi Palace"]
    },
    {
        "name": "Antalya", "state": "Turkey", "avg_travel_cost": 27000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 900.0, "avg_activity_cost": 1000.0, "rating": 4.6, "category": "Beach",
        "best_season": "April to October", "description": "Turkish Riviera with turquoise coast, ancient ruins, beaches, and Mediterranean charm.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 70,
        "beach_score": 0.8, "nature_score": 0.6, "family_score": 0.8,
        "attractions": ["Kaleici Old Town", "Duden Waterfalls", "Konyaalti Beach", "Aspendos Theatre"]
    },
    {
        "name": "Muscat", "state": "Oman", "avg_travel_cost": 32000.0, "avg_hotel_cost": 5000.0,
        "avg_food_cost": 1200.0, "avg_activity_cost": 1500.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "Omani capital with Grand Mosque, desert landscapes, mountains, and traditional souks.",
        "budget_tier": "Mid-range", "recommended_duration": 4, "comfort_level": 75,
        "city_score": 0.7, "religious_score": 0.7, "nature_score": 0.6,
        "attractions": ["Sultan Qaboos Mosque", "Mutrah Souq", "Royal Opera House", "Wadi Shab"]
    },
    {
        "name": "Doha", "state": "Qatar", "avg_travel_cost": 38000.0, "avg_hotel_cost": 7000.0,
        "avg_food_cost": 1800.0, "avg_activity_cost": 2000.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "November to March", "description": "Modern Middle Eastern city with futuristic skyline, museums, desert adventures, and souqs.",
        "budget_tier": "Premium", "recommended_duration": 3, "comfort_level": 90,
        "city_score": 0.8, "family_score": 0.7, "beach_score": 0.5,
        "attractions": ["Museum of Islamic Art", "Souq Waqif", "The Pearl", "Desert Safari"]
    },
    {
        "name": "Petra", "state": "Jordan", "avg_travel_cost": 30000.0, "avg_hotel_cost": 4000.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 1500.0, "rating": 4.9, "category": "Adventure",
        "best_season": "March to May, September to November", "description": "Ancient Nabatean city carved in rose-red cliffs, UNESCO World Wonder.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "adventure_score": 0.9, "religious_score": 0.6, "nature_score": 0.7,
        "attractions": ["The Treasury", "Monastery", "Siq Canyon", "High Place of Sacrifice"]
    },
    {
        "name": "Tel Aviv", "state": "Israel", "avg_travel_cost": 35000.0, "avg_hotel_cost": 6000.0,
        "avg_food_cost": 1500.0, "avg_activity_cost": 1800.0, "rating": 4.6, "category": "City Exploration",
        "best_season": "April to May, October to November", "description": "Mediterranean coastal city with beaches, nightlife, Bauhaus architecture, and tech scene.",
        "budget_tier": "Premium", "recommended_duration": 4, "comfort_level": 80,
        "city_score": 0.8, "beach_score": 0.7, "solo_score": 0.7,
        "attractions": ["Jaffa Old City", "Tel Aviv Beach", "Carmel Market", "White City"]
    },
    {
        "name": "Beirut", "state": "Lebanon", "avg_travel_cost": 29000.0, "avg_hotel_cost": 4000.0,
        "avg_food_cost": 1200.0, "avg_activity_cost": 1000.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "April to June, September to November", "description": "Vibrant Mediterranean capital with nightlife, cuisine, history, and seaside corniche.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 70,
        "city_score": 0.7, "beach_score": 0.5, "solo_score": 0.6,
        "attractions": ["Pigeon Rocks", "National Museum", "Beirut Souks", "Corniche Promenade"]
    },
    {
        "name": "Baku", "state": "Azerbaijan", "avg_travel_cost": 26000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 900.0, "avg_activity_cost": 1000.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "April to June, September to October", "description": "Caspian Sea capital mixing medieval Old City with futuristic Flame Towers.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 70,
        "city_score": 0.7, "religious_score": 0.6, "family_score": 0.6,
        "attractions": ["Old City", "Flame Towers", "Maiden Tower", "Heydar Aliyev Center"]
    },

    # EUROPE (10 destinations)
    {
        "name": "Paris", "state": "France", "avg_travel_cost": 45000.0, "avg_hotel_cost": 8000.0,
        "avg_food_cost": 2500.0, "avg_activity_cost": 2000.0, "rating": 4.9, "category": "City Exploration",
        "best_season": "April to June, September to October", "description": "City of Light with Eiffel Tower, museums, cuisine, fashion, and romantic ambiance.",
        "budget_tier": "Premium", "recommended_duration": 5, "comfort_level": 85,
        "city_score": 0.9, "romantic_score": 0.9, "family_score": 0.8,
        "attractions": ["Eiffel Tower", "Louvre Museum", "Notre Dame", "Champs-Élysées"]
    },
    {
        "name": "London", "state": "UK", "avg_travel_cost": 48000.0, "avg_hotel_cost": 9000.0,
        "avg_food_cost": 2800.0, "avg_activity_cost": 2500.0, "rating": 4.8, "category": "City Exploration",
        "best_season": "May to September", "description": "Historic capital with royal palaces, museums, theatre, markets, and multicultural cuisine.",
        "budget_tier": "Premium", "recommended_duration": 5, "comfort_level": 90,
        "city_score": 0.9, "family_score": 0.8, "solo_score": 0.8,
        "attractions": ["Big Ben", "British Museum", "Tower of London", "Buckingham Palace"]
    },
    {
        "name": "Barcelona", "state": "Spain", "avg_travel_cost": 42000.0, "avg_hotel_cost": 6500.0,
        "avg_food_cost": 2000.0, "avg_activity_cost": 1800.0, "rating": 4.8, "category": "City Exploration",
        "best_season": "May to June, September to October", "description": "Catalan capital with Gaudí architecture, beaches, Gothic quarter, and vibrant culture.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 80,
        "city_score": 0.9, "beach_score": 0.6, "romantic_score": 0.7,
        "attractions": ["Sagrada Familia", "Park Güell", "La Rambla", "Gothic Quarter"]
    },
    {
        "name": "Rome", "state": "Italy", "avg_travel_cost": 43000.0, "avg_hotel_cost": 7000.0,
        "avg_food_cost": 2200.0, "avg_activity_cost": 1800.0, "rating": 4.9, "category": "City Exploration",
        "best_season": "April to June, September to October", "description": "Eternal City with Colosseum, Vatican, ancient ruins, and world-class Italian cuisine.",
        "budget_tier": "Mid-range", "recommended_duration": 5, "comfort_level": 80,
        "city_score": 0.9, "religious_score": 0.8, "family_score": 0.8,
        "attractions": ["Colosseum", "Vatican City", "Trevi Fountain", "Roman Forum"]
    },
    {
        "name": "Amsterdam", "state": "Netherlands", "avg_travel_cost": 44000.0, "avg_hotel_cost": 7500.0,
        "avg_food_cost": 2300.0, "avg_activity_cost": 2000.0, "rating": 4.7, "category": "City Exploration",
        "best_season": "April to May, September to November", "description": "Canal city with museums, bicycles, tulips, liberal culture, and historic architecture.",
        "budget_tier": "Premium", "recommended_duration": 4, "comfort_level": 85,
        "city_score": 0.8, "solo_score": 0.8, "romantic_score": 0.7,
        "attractions": ["Anne Frank House", "Van Gogh Museum", "Canal Cruise", "Rijksmuseum"]
    },
    {
        "name": "Prague", "state": "Czech Republic", "avg_travel_cost": 38000.0, "avg_hotel_cost": 5000.0,
        "avg_food_cost": 1500.0, "avg_activity_cost": 1200.0, "rating": 4.7, "category": "City Exploration",
        "best_season": "April to May, September to October", "description": "Fairytale city with medieval castle, Charles Bridge, beer culture, and Gothic architecture.",
        "budget_tier": "Mid-range", "recommended_duration": 4, "comfort_level": 75,
        "city_score": 0.8, "romantic_score": 0.8, "family_score": 0.7,
        "attractions": ["Prague Castle", "Charles Bridge", "Old Town Square", "Astronomical Clock"]
    },
    {
        "name": "Vienna", "state": "Austria", "avg_travel_cost": 41000.0, "avg_hotel_cost": 6500.0,
        "avg_food_cost": 2000.0, "avg_activity_cost": 1500.0, "rating": 4.7, "category": "City Exploration",
        "best_season": "April to May, September to October", "description": "Imperial city with palaces, classical music, coffee houses, and elegant architecture.",
        "budget_tier": "Mid-range", "recommended_duration": 4, "comfort_level": 85,
        "city_score": 0.8, "romantic_score": 0.8, "family_score": 0.8,
        "attractions": ["Schönbrunn Palace", "St. Stephen's Cathedral", "Hofburg Palace", "Vienna Opera"]
    },
    {
        "name": "Santorini", "state": "Greece", "avg_travel_cost": 40000.0, "avg_hotel_cost": 7000.0,
        "avg_food_cost": 2000.0, "avg_activity_cost": 1500.0, "rating": 4.9, "category": "Beach",
        "best_season": "April to November", "description": "Iconic Greek island with white-washed buildings, blue domes, sunsets, and volcanic beaches.",
        "budget_tier": "Premium", "recommended_duration": 4, "comfort_level": 85,
        "beach_score": 0.8, "romantic_score": 0.9, "nature_score": 0.6,
        "attractions": ["Oia Sunset", "Red Beach", "Akrotiri", "Fira Town"]
    },
    {
        "name": "Reykjavik", "state": "Iceland", "avg_travel_cost": 50000.0, "avg_hotel_cost": 10000.0,
        "avg_food_cost": 3000.0, "avg_activity_cost": 3500.0, "rating": 4.8, "category": "Nature",
        "best_season": "June to August", "description": "Nordic capital gateway to waterfalls, geysers, Northern Lights, and Blue Lagoon.",
        "budget_tier": "Premium", "recommended_duration": 5, "comfort_level": 85,
        "nature_score": 0.9, "adventure_score": 0.8, "solo_score": 0.7,
        "attractions": ["Blue Lagoon", "Golden Circle", "Northern Lights", "Hallgrímskirkja"]
    },
    {
        "name": "Lisbon", "state": "Portugal", "avg_travel_cost": 36000.0, "avg_hotel_cost": 5500.0,
        "avg_food_cost": 1500.0, "avg_activity_cost": 1200.0, "rating": 4.7, "category": "City Exploration",
        "best_season": "March to May, September to October", "description": "Hilly coastal capital with trams, pastel buildings, Fado music, and seafood.",
        "budget_tier": "Mid-range", "recommended_duration": 4, "comfort_level": 75,
        "city_score": 0.8, "beach_score": 0.5, "romantic_score": 0.7,
        "attractions": ["Belém Tower", "Jerónimos Monastery", "Alfama District", "Tram 28"]
    },

    # MORE INDIAN DESTINATIONS (20 destinations)
    {
        "name": "Ladakh", "state": "Jammu & Kashmir", "avg_travel_cost": 8000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.9, "category": "Adventure",
        "best_season": "June to September", "description": "High-altitude desert with monasteries, Pangong Lake, mountain passes, and stark beauty.",
        "budget_tier": "Mid-range", "recommended_duration": 7, "comfort_level": 50,
        "adventure_score": 0.9, "nature_score": 0.9, "religious_score": 0.6,
        "attractions": ["Pangong Lake", "Nubra Valley", "Magnetic Hill", "Thiksey Monastery"]
    },
    {
        "name": "Zanskar Valley", "state": "Jammu & Kashmir", "avg_travel_cost": 9000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1800.0, "rating": 4.8, "category": "Adventure",
        "best_season": "June to September", "description": "Remote Himalayan valley with frozen river trek, monasteries, and rugged landscapes.",
        "budget_tier": "Budget", "recommended_duration": 8, "comfort_level": 45,
        "adventure_score": 0.9, "nature_score": 0.9, "religious_score": 0.5,
        "attractions": ["Chadar Trek", "Phuktal Monastery", "Zanskar River", "Padum"]
    },
    {
        "name": "Tawang", "state": "Arunachal Pradesh", "avg_travel_cost": 7000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 800.0, "rating": 4.7, "category": "Religious",
        "best_season": "March to October", "description": "Remote Buddhist town with India's largest monastery, mountain views, and Sela Pass.",
        "budget_tier": "Budget", "recommended_duration": 5, "comfort_level": 55,
        "religious_score": 0.9, "nature_score": 0.8, "adventure_score": 0.6,
        "attractions": ["Tawang Monastery", "Sela Pass", "Madhuri Lake", "War Memorial"]
    },
    {
        "name": "Sikkim", "state": "Sikkim", "avg_travel_cost": 6000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 900.0, "rating": 4.8, "category": "Nature",
        "best_season": "March to June, September to December", "description": "Himalayan state with Kanchenjunga views, monasteries, alpine lakes, and rhododendrons.",
        "budget_tier": "Mid-range", "recommended_duration": 6, "comfort_level": 65,
        "nature_score": 0.9, "adventure_score": 0.7, "religious_score": 0.6,
        "attractions": ["Gangtok", "Tsomgo Lake", "Nathula Pass", "Rumtek Monastery"]
    },
    {
        "name": "Meghalaya", "state": "Meghalaya", "avg_travel_cost": 5500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 700.0, "rating": 4.7, "category": "Nature",
        "best_season": "October to May", "description": "Wettest place with living root bridges, waterfalls, caves, and lush green hills.",
        "budget_tier": "Budget", "recommended_duration": 5, "comfort_level": 60,
        "nature_score": 0.9, "adventure_score": 0.7, "solo_score": 0.6,
        "attractions": ["Double Decker Root Bridge", "Nohkalikai Falls", "Mawlynnong", "Dawki River"]
    },
    {
        "name": "Spiti Valley", "state": "Himachal Pradesh", "avg_travel_cost": 7500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1200.0, "rating": 4.8, "category": "Adventure",
        "best_season": "May to October", "description": "Cold desert mountain valley with ancient monasteries, stark landscapes, and high passes.",
        "budget_tier": "Budget", "recommended_duration": 7, "comfort_level": 50,
        "adventure_score": 0.9, "nature_score": 0.9, "religious_score": 0.7,
        "attractions": ["Key Monastery", "Chandratal Lake", "Kaza", "Pin Valley"]
    },
    {
        "name": "Rann of Kutch", "state": "Gujarat", "avg_travel_cost": 4500.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1000.0, "rating": 4.6, "category": "Nature",
        "best_season": "November to February", "description": "White salt desert with Rann Utsav festival, crafts, wildlife, and full moon magic.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "nature_score": 0.8, "family_score": 0.7, "adventure_score": 0.5,
        "attractions": ["White Rann", "Rann Utsav", "Kalo Dungar", "Mandvi Beach"]
    },
    {
        "name": "Orchha", "state": "Madhya Pradesh", "avg_travel_cost": 3000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 300.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Medieval town with palaces, temples, cenotaphs along Betwa River, and rural charm.",
        "budget_tier": "Budget", "recommended_duration": 2, "comfort_level": 60,
        "religious_score": 0.7, "nature_score": 0.5, "family_score": 0.6,
        "attractions": ["Orchha Fort", "Ram Raja Temple", "Betwa River", "Chaturbhuj Temple"]
    },
    {
        "name": "Khajuraho", "state": "Madhya Pradesh", "avg_travel_cost": 3200.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 400.0, "rating": 4.6, "category": "Religious",
        "best_season": "October to March", "description": "UNESCO site with exquisite erotic sculptures on ancient temples from Chandela dynasty.",
        "budget_tier": "Budget", "recommended_duration": 2, "comfort_level": 60,
        "religious_score": 0.8, "family_score": 0.5, "city_score": 0.4,
        "attractions": ["Western Group Temples", "Kandariya Temple", "Light & Sound Show", "Raneh Falls"]
    },
    {
        "name": "Konark", "state": "Odisha", "avg_travel_cost": 2800.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 300.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Sun Temple UNESCO site with chariot architecture, beach, and Odissi dance heritage.",
        "budget_tier": "Budget", "recommended_duration": 2, "comfort_level": 55,
        "religious_score": 0.8, "beach_score": 0.5, "family_score": 0.6,
        "attractions": ["Sun Temple", "Konark Beach", "ASI Museum", "Chandrabhaga Beach"]
    },
    {
        "name": "Hampi", "state": "Karnataka", "avg_travel_cost": 3500.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 400.0, "rating": 4.7, "category": "Religious",
        "best_season": "October to February", "description": "Vijayanagara ruins with boulder landscapes, ancient temples, hippie island, and history.",
        "budget_tier": "Budget", "recommended_duration": 3, "comfort_level": 55,
        "religious_score": 0.8, "adventure_score": 0.6, "solo_score": 0.7,
        "attractions": ["Virupaksha Temple", "Stone Chariot", "Vittala Temple", "Hippie Island"]
    },
    {
        "name": "Badami", "state": "Karnataka", "avg_travel_cost": 3200.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 300.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Cave temples carved in red sandstone cliffs, ancient Chalukya capital, Agastya Lake.",
        "budget_tier": "Budget", "recommended_duration": 2, "comfort_level": 50,
        "religious_score": 0.8, "nature_score": 0.5, "adventure_score": 0.5,
        "attractions": ["Badami Cave Temples", "Agastya Lake", "Banashankari Temple", "Pattadakal"]
    },
    {
        "name": "Alleppey", "state": "Kerala", "avg_travel_cost": 3800.0, "avg_hotel_cost": 4000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.7, "category": "Romantic",
        "best_season": "November to February", "description": "Venice of East with backwater houseboats, canals, paddy fields, and tranquil cruises.",
        "budget_tier": "Mid-range", "recommended_duration": 2, "comfort_level": 75,
        "romantic_score": 0.9, "nature_score": 0.7, "family_score": 0.6,
        "attractions": ["Houseboat Cruise", "Vembanad Lake", "Alappuzha Beach", "Backwater Villages"]
    },
    {
        "name": "Thekkady", "state": "Kerala", "avg_travel_cost": 4000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 900.0, "rating": 4.6, "category": "Nature",
        "best_season": "September to March", "description": "Periyar Wildlife Sanctuary with spice plantations, elephant rides, and lake cruises.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "nature_score": 0.9, "adventure_score": 0.6, "family_score": 0.7,
        "attractions": ["Periyar Lake", "Spice Plantations", "Elephant Ride", "Bamboo Rafting"]
    },
    {
        "name": "Chikmagalur", "state": "Karnataka", "avg_travel_cost": 3500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 600.0, "rating": 4.6, "category": "Nature",
        "best_season": "September to May", "description": "Coffee land with hill stations, waterfalls, trekking trails, and aromatic plantations.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "nature_score": 0.8, "adventure_score": 0.6, "romantic_score": 0.6,
        "attractions": ["Mullayanagiri Peak", "Coffee Plantations", "Baba Budangiri", "Hebbe Falls"]
    },
    {
        "name": "Kabini", "state": "Karnataka", "avg_travel_cost": 4500.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.6, "category": "Nature",
        "best_season": "October to May", "description": "Wildlife sanctuary with jungle safaris, elephant sightings, river, and luxury resorts.",
        "budget_tier": "Mid-range", "recommended_duration": 2, "comfort_level": 75,
        "nature_score": 0.9, "adventure_score": 0.6, "family_score": 0.7,
        "attractions": ["Nagarhole National Park", "Kabini River", "Wildlife Safari", "Coracle Ride"]
    },
    {
        "name": "Bandhavgarh", "state": "Madhya Pradesh", "avg_travel_cost": 5000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1800.0, "rating": 4.7, "category": "Nature",
        "best_season": "October to June", "description": "Tiger reserve with highest density of tigers, ancient fort, and jungle safaris.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 65,
        "nature_score": 0.9, "adventure_score": 0.7, "family_score": 0.6,
        "attractions": ["Tiger Safari", "Bandhavgarh Fort", "Tala Zone", "Bird Watching"]
    },
    {
        "name": "Ranthambore", "state": "Rajasthan", "avg_travel_cost": 4500.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1600.0, "rating": 4.7, "category": "Nature",
        "best_season": "October to April", "description": "Famous tiger reserve with historic fort ruins, lakes, and royal hunting grounds.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 70,
        "nature_score": 0.9, "adventure_score": 0.6, "family_score": 0.7,
        "attractions": ["Tiger Safari", "Ranthambore Fort", "Padam Talao", "Jogi Mahal"]
    },
    {
        "name": "Jim Corbett", "state": "Uttarakhand", "avg_travel_cost": 4000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.6, "category": "Nature",
        "best_season": "November to June", "description": "India's oldest national park with tigers, elephants, river rafting, and eco-tourism.",
        "budget_tier": "Mid-range", "recommended_duration": 3, "comfort_level": 70,
        "nature_score": 0.9, "adventure_score": 0.7, "family_score": 0.7,
        "attractions": ["Dhikala Zone", "Corbett Falls", "Garjiya Temple", "River Rafting"]
    },
    {
        "name": "Valley of Flowers", "state": "Uttarakhand", "avg_travel_cost": 6000.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 1000.0, "rating": 4.8, "category": "Nature",
        "best_season": "July to September", "description": "UNESCO park with alpine flowers, meadows, glaciers, and Hemkund Sahib trek.",
        "budget_tier": "Budget", "recommended_duration": 5, "comfort_level": 50,
        "nature_score": 0.9, "adventure_score": 0.8, "religious_score": 0.6,
        "attractions": ["Flower Meadows", "Hemkund Sahib", "Pushpawati River", "Trek Route"]
    }
]

def seed_enhanced_destinations(db: Session):
    """Add international and additional Indian destinations to database"""
    count = 0
    for dest_data in INTERNATIONAL_DESTINATIONS:
        existing = db.query(Destination).filter(
            Destination.name == dest_data["name"],
            Destination.state == dest_data["state"]
        ).first()
        
        if not existing:
            destination = Destination(**dest_data)
            db.add(destination)
            count += 1
    
    db.commit()
    return count
