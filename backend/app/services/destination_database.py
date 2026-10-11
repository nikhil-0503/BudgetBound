"""
Destination-specific activity database for fallback itinerary generation.
Provides real attractions, dining, transport options, and cost estimates for Indian destinations.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Activity:
    """A specific destination activity."""
    title: str
    description: str
    location: str  # Specific neighborhood or landmark
    estimated_cost: float
    duration_minutes: int
    best_time: str  # "morning", "afternoon", "evening"
    category: str  # "heritage", "nature", "food", "culture", "adventure", "market", "leisure"
    vegetarian_friendly: bool = False
    requires_booking: bool = False
    wheelchair_accessible: bool = False


@dataclass
class Restaurant:
    """A specific restaurant or dining venue."""
    name: str
    location: str
    cuisine: str
    avg_cost_per_person: float
    vegetarian_options: bool
    specialties: List[str]  # e.g., ["Butter Chicken", "Chole Bhature"]


@dataclass  
class TransferRoute:
    """Transport between two cities."""
    origin: str
    destination: str
    transport_modes: List[Dict[str, any]]  # [{"mode": "train", "duration_hours": 3.5, "cost_per_person": 400}, ...]


# ============================================================================
# INDIAN DESTINATIONS DATABASE
# ============================================================================

DESTINATIONS_DB = {
    "delhi": {
        "common_names": ["delhi", "new delhi", "delhi ncr"],
        "activities": [
            Activity(
                title="Sunrise walk around India Gate & Central Vista",
                description="Start your day with a peaceful walk around the iconic India Gate monument and the surrounding Central Vista park. Great for photography and morning jogging.",
                location="Central Delhi (India Gate, Parliament Street)",
                estimated_cost=0.0,
                duration_minutes=90,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Visit Red Fort & Chandni Chowk old market",
                description="Explore the UNESCO World Heritage Red Fort, then navigate the chaotic but vibrant Chandni Chowk bazaar packed with street food, textiles, and jewelry vendors.",
                location="Old Delhi (Red Fort, Chandni Chowk)",
                estimated_cost=250.0,  # Includes entry fee
                duration_minutes=180,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=False,
                wheelchair_accessible=False
            ),
            Activity(
                title="Jama Masjid & spice market exploration",
                description="Visit India's largest mosque, then explore the aromatic spice market (Jain Sarak) nearby. Climb the minaret for city views (₹100 extra).",
                location="Old Delhi (Jama Masjid area)",
                estimated_cost=100.0,
                duration_minutes=120,
                best_time="late_morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Qutub Minar & Mehrauli Archaeological Park",
                description="India's tallest brick minaret (73m) surrounded by ruins of seven historic cities. Well-maintained park with local cafes.",
                location="South Delhi (Mehrauli)",
                estimated_cost=300.0,  # Includes entry + travel
                duration_minutes=150,
                best_time="afternoon",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Humayun's Tomb & Lodi Gardens walk",
                description="Stunning Mughal mausoleum set in sprawling gardens. Less crowded than other monuments. Great for photography.",
                location="Central Delhi (Lodi Gardens area)",
                estimated_cost=200.0,
                duration_minutes=120,
                best_time="afternoon",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="National Museum guided tour",
                description="3-hour guided tour covering Indian art, artifacts from Mughal era, Indus Valley Civilization finds. Skip if short on time.",
                location="Rajpath, Central Delhi",
                estimated_cost=400.0,
                duration_minutes=180,
                best_time="morning_or_afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Street food tour in Karol Bagh market",
                description="Guided or self-guided exploration of famous street food vendors. Try pani puri, gol gappas, samosas, jalebis. Can be spicy.",
                location="Karol Bagh (West Delhi)",
                estimated_cost=250.0,
                duration_minutes=90,
                best_time="evening",
                category="food",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Sunset at Raj Ghat & evening stroll",
                description="Simple but poignant Gandhi memorial. Peaceful especially at sunset. Adjacent to Yamuna riverbank.",
                location="East Delhi (Raj Ghat)",
                estimated_cost=0.0,
                duration_minutes=60,
                best_time="evening",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
        ],
        "restaurants": [
            Restaurant(
                name="Karims Restaurant",
                location="Jama Masjid area, Old Delhi",
                cuisine="Mughlai (non-veg)",
                avg_cost_per_person=350.0,
                vegetarian_options=False,
                specialties=["Nihari", "Korma", "Shami Kebab"]
            ),
            Restaurant(
                name="Aroma Restaurant",
                location="Khan Market, Central Delhi",
                cuisine="Multi-cuisine",
                avg_cost_per_person=600.0,
                vegetarian_options=True,
                specialties=["Butter Chicken", "Paneer Tikka", "Biryani"]
            ),
            Restaurant(
                name="Dilli Haat Food Court",
                location="Dilli Haat, INA Market",
                cuisine="Indian street food",
                avg_cost_per_person=200.0,
                vegetarian_options=True,
                specialties=["Chole Bhature", "Idli", "Dosa", "Chaat"]
            ),
            Restaurant(
                name="Indian Accent",
                location="The Lodhi Hotel, Lodhi Road",
                cuisine="Contemporary Indian",
                avg_cost_per_person=1200.0,
                vegetarian_options=True,
                specialties=["Modern Indian cuisine", "Tasting menus"]
            ),
        ],
        "transport_modes": [
            {"mode": "metro", "cost_range": (10, 50), "frequency": "every_2_minutes", "coverage": "excellent"},
            {"mode": "auto_rickshaw", "cost_range": (40, 150), "frequency": "on_demand", "coverage": "good"},
            {"mode": "taxi", "cost_range": (150, 400), "frequency": "on_demand", "coverage": "excellent"},
            {"mode": "bus", "cost_range": (5, 20), "frequency": "every_5_minutes", "coverage": "excellent"},
        ],
        "cost_of_living": "budget",  # "budget", "mid_range", "expensive"
        "best_time": "October-March (cool weather)",
        "highlights": ["Red Fort", "India Gate", "Qutub Minar", "Chandni Chowk"],
        "must_try_food_non_veg": ["Nihari", "Butter Chicken", "Tandoori Chicken"],
        "must_try_food_veg": ["Chole Bhature", "Aloo Parathas", "Paneer Tikka"],
    },
    
    "agra": {
        "common_names": ["agra", "taj mahal"],
        "activities": [
            Activity(
                title="Sunrise at Taj Mahal",
                description="Book tickets in advance. Arrive by 5 AM to see the monument in soft morning light before crowds arrive. Most magical time.",
                location="Taj Mahal (South bank of Yamuna)",
                estimated_cost=500.0,  # Including guide
                duration_minutes=180,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Agra Fort & government museum",
                description="Red sandstone fort with intricate inlay work. Museum has Mughal artifacts, weapons, and manuscripts.",
                location="Agra Fort (North bank of Yamuna)",
                estimated_cost=250.0,
                duration_minutes=120,
                best_time="afternoon",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Mehtab Bagh sunset viewpoint",
                description="Less crowded Taj Mahal view from the opposite bank. Beautiful during golden hour. Local tea stalls nearby.",
                location="Mehtab Bagh (North bank of Yamuna)",
                estimated_cost=100.0,
                duration_minutes=90,
                best_time="evening",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Local market walk & inlay handicrafts",
                description="Explore Kinari Bazaar for traditional Agra inlay work (marble with semi-precious stones). Haggling expected. Visit workshops.",
                location="Kinari Bazaar, Central Agra",
                estimated_cost=200.0,  # Budget for purchases
                duration_minutes=120,
                best_time="afternoon",
                category="market",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Fatehpur Sikri day trip",
                description="UNESCO site 37 km away. Abandoned 16th century Mughal city with intact palaces, mosques, courtyards. Hire local guide.",
                location="Fatehpur Sikri (37 km from Agra)",
                estimated_cost=600.0,  # Includes transport + guide
                duration_minutes=480,
                best_time="full_day",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
        ],
        "restaurants": [
            Restaurant(
                name="Pinch of Spice",
                location="Fatehabad Road, Agra",
                cuisine="North Indian",
                avg_cost_per_person=300.0,
                vegetarian_options=True,
                specialties=["Butter Chicken", "Chole Bhature", "Biryani"]
            ),
            Restaurant(
                name="Dasaprakash",
                location="Gwalior Road, Agra",
                cuisine="South Indian",
                avg_cost_per_person=250.0,
                vegetarian_options=True,
                specialties=["Dosa", "Idli", "Sambar", "South Indian Thali"]
            ),
        ],
        "transport_modes": [
            {"mode": "train", "cost_range": (100, 300), "frequency": "hourly", "coverage": "delhi_and_jaipur"},
            {"mode": "bus", "cost_range": (150, 400), "frequency": "every_30_min", "coverage": "delhi_and_jaipur"},
            {"mode": "cab", "cost_range": (2000, 3500), "frequency": "on_demand", "coverage": "local"},
        ],
        "cost_of_living": "budget",
        "best_time": "October-March",
        "highlights": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri"],
        "must_try_food_non_veg": ["Tandoori Chicken", "Nihari"],
        "must_try_food_veg": ["Aloo Parathas", "Paneer Tikka"],
    },

    "jaipur": {
        "common_names": ["jaipur", "pink city"],
        "activities": [
            Activity(
                title="Hawa Mahal (Palace of Winds) & City Palace",
                description="Iconic 5-story pink terracotta structure (1799) with 953 small windows. Combine with adjacent City Palace tour.",
                location="Badi Chaupad, Central Jaipur",
                estimated_cost=300.0,
                duration_minutes=120,
                best_time="morning_or_afternoon",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Albert Hall Museum",
                description="Central India Museum with Mughal & Rajasthani artifacts, sculptures, pottery. Well-maintained, air-conditioned.",
                location="Ram Niwas Garden, Central Jaipur",
                estimated_cost=300.0,
                duration_minutes=120,
                best_time="afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Jantar Mantar (astronomical observation instrument)",
                description="UNESCO World Heritage Site. 18th-century astronomical instrument garden with 19 structures. Guide highly recommended.",
                location="Near City Palace, Central Jaipur",
                estimated_cost=250.0,
                duration_minutes=90,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Nahargarh Fort & sunset viewpoint",
                description="Hilltop fort overlooking the entire pink city. Accessible by car or 45-min hike. Best at sunset.",
                location="Aravalli Hills, North Jaipur",
                estimated_cost=150.0,  # Including entry + vehicle
                duration_minutes=120,
                best_time="evening",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Local textile & traditional blue pottery workshop",
                description="Visit working studios of traditional indigo printers and blue pottery artisans. Can purchase directly from makers.",
                location="Bagru or Kripal Kumbh area",
                estimated_cost=400.0,
                duration_minutes=150,
                best_time="morning_or_afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
        ],
        "restaurants": [
            Restaurant(
                name="Chokhi Dhani",
                location="RIICO Industrial Area, Sitapura, Jaipur",
                cuisine="Rajasthani",
                avg_cost_per_person=400.0,
                vegetarian_options=True,
                specialties=["Gatte ki Sabzi", "Laal Maas", "Bajra Roti", "Rajasthani Thali"]
            ),
            Restaurant(
                name="Surya Niwas",
                location="C-Scheme, Jaipur",
                cuisine="Continental & Indian",
                avg_cost_per_person=500.0,
                vegetarian_options=True,
                specialties=["Butter Chicken", "Paneer Dishes", "Indian Breads"]
            ),
        ],
        "transport_modes": [
            {"mode": "train", "cost_range": (150, 400), "frequency": "multiple_daily", "coverage": "delhi_and_agra"},
            {"mode": "bus", "cost_range": (200, 500), "frequency": "every_30_min", "coverage": "delhi_and_agra"},
            {"mode": "taxi", "cost_range": (300, 600), "frequency": "on_demand", "coverage": "local"},
        ],
        "cost_of_living": "budget",
        "best_time": "October-March",
        "highlights": ["Hawa Mahal", "City Palace", "Jantar Mantar", "Nahargarh Fort"],
        "must_try_food_non_veg": ["Laal Maas", "Tandoori"],
        "must_try_food_veg": ["Gatte ki Sabzi", "Dal Baati Churma"],
    },

    "kolkata": {
        "common_names": ["kolkata", "calcutta"],
        "activities": [
            Activity(
                title="Victoria Memorial sunrise & morning tea",
                description="Iconic white marble monument. Morning is best for avoiding crowds and photography. Local tea stalls inside gardens.",
                location="Victoria Memorial area, South Kolkata",
                estimated_cost=200.0,
                duration_minutes=90,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Howrah Bridge & riverfront walk",
                description="Historic cantilever bridge with unique architecture. Early morning or evening walk on the bridge offers views of Hooghly River.",
                location="Howrah Bridge, Central Kolkata",
                estimated_cost=0.0,
                duration_minutes=60,
                best_time="morning_or_evening",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Indian Museum (oldest in Asia)",
                description="Natural history museum with Egyptian mummies, fossils, sculptures, minerals. Sections on Indian history and art.",
                location="Chowringhee Road, Central Kolkata",
                estimated_cost=100.0,
                duration_minutes=120,
                best_time="afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Dakshineswar Kali Temple & river cruise",
                description="Important pilgrimage site where Ramakrishna Paramahamsa served. Scenic location on Hooghly River. Boat rides available.",
                location="North Kolkata (Dakshineswar)",
                estimated_cost=200.0,  # Including boat ride
                duration_minutes=120,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Bengali street food tour (Kolkata specialties)",
                description="Famous for luchi-alur dom, puchka, kati roll, jhal muri. Street food vendors concentrated in specific market areas.",
                location="Multiple locations (Sealdah, BBD Bagh area)",
                estimated_cost=200.0,
                duration_minutes=90,
                best_time="afternoon_or_evening",
                category="food",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Rabindranath Tagore's house (Jorasanko Thakurbari)",
                description="Historic ancestral home of Nobel laureate poet. Preserved with period furniture, manuscripts, and personal memorabilia.",
                location="Jorasanko, North Kolkata",
                estimated_cost=150.0,
                duration_minutes=90,
                best_time="morning_or_afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
        ],
        "restaurants": [
            Restaurant(
                name="6 Ballygunge Place",
                location="Ballygunge, South Kolkata",
                cuisine="Bengali",
                avg_cost_per_person=400.0,
                vegetarian_options=True,
                specialties=["Hilsa Fish Curry", "Luchi-Alur Dom", "Mishti Dohi", "Sandesh"]
            ),
            Restaurant(
                name="Mocambo",
                location="Park Street, Central Kolkata",
                cuisine="Continental & Bengali",
                avg_cost_per_person=600.0,
                vegetarian_options=True,
                specialties=["Chow Mein", "Butter Chicken", "Biryanis"]
            ),
            Restaurant(
                name="Nizam's Kathi Kabab",
                location="Multiple locations in Kolkata",
                cuisine="Street food (Kathi Rolls)",
                avg_cost_per_person=100.0,
                vegetarian_options=True,
                specialties=["Chicken Roll", "Paneer Roll", "Egg Roll"]
            ),
        ],
        "transport_modes": [
            {"mode": "train", "cost_range": (200, 600), "frequency": "multiple_daily", "coverage": "delhi_varanasi_guwahati"},
            {"mode": "metro", "cost_range": (5, 20), "frequency": "every_3_minutes", "coverage": "excellent_limited_lines"},
            {"mode": "bus", "cost_range": (5, 15), "frequency": "every_5_minutes", "coverage": "excellent"},
            {"mode": "taxi", "cost_range": (100, 300), "frequency": "on_demand", "coverage": "good"},
        ],
        "cost_of_living": "budget",
        "best_time": "October-March",
        "highlights": ["Victoria Memorial", "Howrah Bridge", "Indian Museum", "Dakshineswar Temple"],
        "must_try_food_non_veg": ["Hilsa Fish Curry", "Tandoori"],
        "must_try_food_veg": ["Luchi-Alur Dom", "Puchka", "Sandesh"],
    },

    "goa": {
        "common_names": ["goa", "panaji"],
        "activities": [
            Activity(
                title="Arambol Beach morning walk & swimming",
                description="Long stretches of pristine sand, calm waters suitable for swimming. Quieter than South Goa beaches. Seafood shacks nearby.",
                location="Arambol Beach, North Goa",
                estimated_cost=0.0,
                duration_minutes=120,
                best_time="morning",
                category="leisure",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Se Cathedral (Portuguese heritage)",
                description="Largest church in Asia, built in 1652. Gothic architecture, intricate wooden floor, bell tower. Guides available.",
                location="Old Goa (SE Cathedral area)",
                estimated_cost=0.0,  # Free entry
                duration_minutes=90,
                best_time="morning_or_afternoon",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Dudhsagar Waterfall trek (challenging)",
                description="Iconic 600-meter waterfall during monsoon season. Requires 2-3 hour trek. Can hire jeep for part of journey.",
                location="Bhagwan Mahaveer Sanctuary (40 km from Panaji)",
                estimated_cost=800.0,  # Including guide & vehicle
                duration_minutes=300,
                best_time="monsoon_season_july_september",
                category="adventure",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Spice plantation tour",
                description="Visit working cardamom, cinnamon, nutmeg plantations. Learn about processing. Most tours include lunch cooked with plantation ingredients.",
                location="Sahakari Spice Farm or similar (30 km inland)",
                estimated_cost=600.0,
                duration_minutes=180,
                best_time="morning_or_afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Sunset at Palolem Beach & beach shacks",
                description="South Goa's most beautiful beach. Relaxed atmosphere. Watch sunset from beach shacks with beer or coconut water.",
                location="Palolem Beach, South Goa",
                estimated_cost=150.0,  # Food/drinks at beach shacks
                duration_minutes=120,
                best_time="evening",
                category="leisure",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
        ],
        "restaurants": [
            Restaurant(
                name="Fisherman's Wharf",
                location="Panjim (Panaji), Central Goa",
                cuisine="Goan & Seafood",
                avg_cost_per_person=500.0,
                vegetarian_options=True,
                specialties=["Goan Fish Curry", "Prawns Xec Xec", "Sorpotel", "Vindaloo"]
            ),
            Restaurant(
                name="Thalassa Greek Restaurant",
                location="Arambol Beach, North Goa",
                cuisine="Greek & Goan",
                avg_cost_per_person=600.0,
                vegetarian_options=True,
                specialties=["Grilled Fish", "Greek Salads", "Moussaka"]
            ),
        ],
        "transport_modes": [
            {"mode": "train", "cost_range": (300, 800), "frequency": "multiple_daily", "coverage": "delhi_mumbai_bangalore"},
            {"mode": "bus", "cost_range": (200, 600), "frequency": "every_1_hour", "coverage": "delhi_mumbai_bangalore"},
            {"mode": "flight", "cost_range": (2000, 5000), "frequency": "multiple_daily", "coverage": "major_cities"},
            {"mode": "taxi", "cost_range": (400, 1000), "frequency": "on_demand", "coverage": "local"},
        ],
        "cost_of_living": "mid_range",  # Tourist premium
        "best_time": "November-February (cool, dry)",
        "highlights": ["Palolem Beach", "Se Cathedral", "Dudhsagar Waterfall", "Spice Plantations"],
        "must_try_food_non_veg": ["Goan Fish Curry", "Prawns Xec Xec", "Sorpotel"],
        "must_try_food_veg": ["Goan Vegetable Curry", "Poi Bread"],
    },

    "varanasi": {
        "common_names": ["varanasi", "benares", "kashi"],
        "activities": [
            Activity(
                title="Ghat walk at dawn & Ganges ritual observation",
                description="Start before sunrise (5-6 AM) to watch pilgrims perform rituals, priests offer prayers at Dashashwamedh Ghat. Sacred and atmospheric.",
                location="Dashaswamedh Ghat & surrounding ghats, Varanasi",
                estimated_cost=200.0,  # Guide + boat if desired
                duration_minutes=120,
                best_time="early_morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=True
            ),
            Activity(
                title="Kashi Vishwanath Temple & pilgrimage",
                description="One of Hinduism's most sacred temples. Arrive early to avoid queues (often 2-3 hour wait mid-day). Entry through Ghat area.",
                location="Kashi Vishwanath Temple, Central Varanasi",
                estimated_cost=0.0,  # Free entry
                duration_minutes=120,
                best_time="morning",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False  # Narrow lanes, steps
            ),
            Activity(
                title="Boat ride on Ganges (evening aarti ceremony)",
                description="Evening boat ride to Dashashwamedh Ghat to watch the famous Ganga Aarti (prayer ritual). Book in advance.",
                location="Ganges River, Central Varanasi",
                estimated_cost=400.0,
                duration_minutes=90,
                best_time="evening",
                category="heritage",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
            Activity(
                title="Local market walk & cloth dyeing workshop",
                description="Explore narrow lanes of Varanasi bazaar. Visit Banarasi silk weaving workshops (still functional). Can watch artisans at work.",
                location="Varanasi Old City Markets",
                estimated_cost=300.0,  # Purchases
                duration_minutes=120,
                best_time="morning_or_afternoon",
                category="culture",
                vegetarian_friendly=True,
                wheelchair_accessible=False
            ),
        ],
        "restaurants": [
            Restaurant(
                name="Puran Chai",
                location="Dashashwamedh Ghat area, Varanasi",
                cuisine="Vegetarian Street Food",
                avg_cost_per_person=100.0,
                vegetarian_options=True,
                specialties=["Masala Chai", "Kachori", "Jalebi"]
            ),
            Restaurant(
                name="Dolphin Restaurant",
                location="Assi Ghat area, Varanasi",
                cuisine="Indian",
                avg_cost_per_person=250.0,
                vegetarian_options=True,
                specialties=["Aloo Parathas", "Dal Makhani", "Paneer Tikka"]
            ),
        ],
        "transport_modes": [
            {"mode": "train", "cost_range": (200, 600), "frequency": "multiple_daily", "coverage": "delhi_kolkata_mumbai"},
            {"mode": "flight", "cost_range": (2000, 5000), "frequency": "multiple_daily", "coverage": "major_cities"},
            {"mode": "taxi", "cost_range": (150, 400), "frequency": "on_demand", "coverage": "local"},
        ],
        "cost_of_living": "budget",
        "best_time": "October-March",
        "highlights": ["Dashashwamedh Ghat", "Kashi Vishwanath Temple", "Ganges Aarti", "Banarasi Silk"],
        "must_try_food_non_veg": ["Fish Curry"],
        "must_try_food_veg": ["Aloo Parathas", "Chole Bhature", "Jalebi"],
    },
}


def get_destination_info(destination: str) -> Optional[Dict]:
    """Get database entry for a destination (case-insensitive, fuzzy match)."""
    dest_lower = destination.lower().strip()
    
    # Exact match
    if dest_lower in DESTINATIONS_DB:
        return DESTINATIONS_DB[dest_lower]
    
    # Fuzzy match on common names
    for db_key, db_entry in DESTINATIONS_DB.items():
        common_names = db_entry.get("common_names", [])
        if dest_lower in common_names:
            return db_entry
        # Partial match
        for name in common_names:
            if dest_lower in name or name in dest_lower:
                return db_entry
    
    return None


def get_activities_for_destination(destination: str, category: Optional[str] = None, 
                                  vegetarian_only: bool = False, count: int = 3) -> List[Activity]:
    """Get activities for a destination, filtered by preferences."""
    db_entry = get_destination_info(destination)
    if not db_entry:
        return []
    
    activities = db_entry.get("activities", [])
    
    # Filter by category if specified
    if category:
        activities = [a for a in activities if a.category == category]
    
    # Filter by vegetarian if specified
    if vegetarian_only:
        activities = [a for a in activities if a.vegetarian_friendly]
    
    # Return up to `count` activities
    return activities[:count]


def get_restaurants_for_destination(destination: str, vegetarian_only: bool = False) -> List[Restaurant]:
    """Get restaurants for a destination."""
    db_entry = get_destination_info(destination)
    if not db_entry:
        return []
    
    restaurants = db_entry.get("restaurants", [])
    
    if vegetarian_only:
        restaurants = [r for r in restaurants if r.vegetarian_options]
    
    return restaurants


def get_must_try_food(destination: str, vegetarian: bool = True) -> List[str]:
    """Get must-try foods for a destination based on dietary preference."""
    db_entry = get_destination_info(destination)
    if not db_entry:
        return []
    
    if vegetarian:
        return db_entry.get("must_try_food_veg", [])
    else:
        return db_entry.get("must_try_food_non_veg", [])
