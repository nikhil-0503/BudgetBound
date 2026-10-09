from sqlalchemy.orm import Session
from app.models import Destination
from app.seed_enhanced import INTERNATIONAL_DESTINATIONS

DESTINATIONS_DATA = [
    # BEACH (15)
    {
        "name": "North Goa", "state": "Goa", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 600.0, "rating": 4.5, "category": "Beach",
        "best_season": "November to February", "description": "Famed for its beaches, vibrant nightlife, shacks, and water sports.",
        "attractions": ["Baga Beach", "Anjuna Beach", "Fort Aguada", "Calangute Beach"]
    },
    {
        "name": "South Goa", "state": "Goa", "avg_travel_cost": 3000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 500.0, "rating": 4.6, "category": "Beach",
        "best_season": "November to February", "description": "Quiet, pristine sandy beaches and luxury resorts offering relaxed vibes.",
        "attractions": ["Palolem Beach", "Colva Beach", "Cabo de Rama Fort", "Agonda Beach"]
    },
    {
        "name": "Gokarna", "state": "Karnataka", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "Beach",
        "best_season": "October to March", "description": "A temple town with pristine, half-moon shaped beaches and laid-back hostels.",
        "attractions": ["Om Beach", "Kudle Beach", "Mahabaleshwar Temple", "Half Moon Beach"]
    },
    {
        "name": "Varkala", "state": "Kerala", "avg_travel_cost": 3500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Beach",
        "best_season": "October to March", "description": "Unique red cliffs bordering the Arabian Sea, known for hippie culture and spas.",
        "attractions": ["Varkala Cliff", "Papanasam Beach", "Janardhana Swamy Temple", "Anjengo Fort"]
    },
    {
        "name": "Havelock Island", "state": "Andaman & Nicobar", "avg_travel_cost": 8000.0, "avg_hotel_cost": 4500.0,
        "avg_food_cost": 1200.0, "avg_activity_cost": 2000.0, "rating": 4.8, "category": "Beach",
        "best_season": "October to May", "description": "World-famous Radhanagar beach, scuba diving sites, and turquoise waters.",
        "attractions": ["Radhanagar Beach", "Elephant Beach", "Vijay Nagar Beach", "Neil Island ferry"]
    },
    {
        "name": "Pondicherry", "state": "Tamil Nadu", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "Beach",
        "best_season": "October to March", "description": "A charming French colony with cobble-stone streets, cafes, and peaceful rock beaches.",
        "attractions": ["Promenade Beach", "Auroville", "French Quarter", "Paradise Beach"]
    },
    {
        "name": "Kovalam", "state": "Kerala", "avg_travel_cost": 3500.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 750.0, "avg_activity_cost": 500.0, "rating": 4.4, "category": "Beach",
        "best_season": "November to February", "description": "An internationally renowned beach destination with three adjacent crescent beaches.",
        "attractions": ["Lighthouse Beach", "Hawah Beach", "Samudra Beach", "Halcyon Castle"]
    },
    {
        "name": "Alibaug", "state": "Maharashtra", "avg_travel_cost": 1200.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 400.0, "rating": 4.1, "category": "Beach",
        "best_season": "November to March", "description": "A popular weekend getaway with sandy black beaches and historic sea forts.",
        "attractions": ["Kashid Beach", "Kolaba Fort", "Alibaug Beach", "Murud Janjira Fort"]
    },
    {
        "name": "Mahabalipuram", "state": "Tamil Nadu", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "Beach",
        "best_season": "October to March", "description": "Known for its UNESCO heritage rock-cut temples, stone carving workshops, and surfing.",
        "attractions": ["Shore Temple", "Five Rathas", "Krishna's Butterball", "Mahabalipuram Beach"]
    },
    {
        "name": "Puri Beach", "state": "Odisha", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 250.0, "rating": 4.2, "category": "Beach",
        "best_season": "October to February", "description": "A sacred beach destination on the Bay of Bengal, famous for sand art and high tides.",
        "attractions": ["Puri Beach", "Golden Beach", "Jagannath Temple", "Swargadwar Beach"]
    },
    {
        "name": "Daman", "state": "Daman & Diu", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 300.0, "rating": 4.1, "category": "Beach",
        "best_season": "October to March", "description": "A quiet coastal union territory with Portuguese forts, palm-lined shores, and relaxed promenades.",
        "attractions": ["Devka Beach", "Jampore Beach", "Fort of Moti Daman", "Mirasol Lake Garden"]
    },
    {
        "name": "Tarkarli", "state": "Maharashtra", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 900.0, "rating": 4.5, "category": "Beach",
        "best_season": "October to March", "description": "Crystal-clear waters ideal for scuba diving, houseboats, and Sindhudurg fort excursions.",
        "attractions": ["Tarkarli Beach", "Scuba Diving Point", "Sindhudurg Fort", "Devbag Beach"]
    },
    {
        "name": "Neil Island", "state": "Andaman & Nicobar", "avg_travel_cost": 7500.0, "avg_hotel_cost": 3800.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 1800.0, "rating": 4.6, "category": "Beach",
        "best_season": "October to May", "description": "A slow-paced island paradise with coral reefs, lagoons, and bicycle-friendly village roads.",
        "attractions": ["Bharatpur Beach", "Laxmanpur Beach", "Natural Bridge", "Sitapur Beach"]
    },
    {
        "name": "Diu", "state": "Daman & Diu", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 350.0, "rating": 4.2, "category": "Beach",
        "best_season": "October to March", "description": "A fortified island town blending Portuguese heritage with calm beaches and seafood shacks.",
        "attractions": ["Nagoa Beach", "Diu Fort", "St. Paul's Church", "Ghogla Beach"]
    },
    {
        "name": "Lakshadweep", "state": "Lakshadweep", "avg_travel_cost": 9000.0, "avg_hotel_cost": 5000.0,
        "avg_food_cost": 1100.0, "avg_activity_cost": 2200.0, "rating": 4.7, "category": "Beach",
        "best_season": "October to May", "description": "Remote coral atolls with turquoise lagoons, snorkeling, and pristine white-sand beaches.",
        "attractions": ["Bangaram Island", "Agatti Lagoon", "Kadmat Beach", "Scuba Reefs"]
    },

    # NATURE (15)
    {
        "name": "Munnar", "state": "Kerala", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.7, "category": "Nature",
        "best_season": "September to May", "description": "Stunning hill station carpeted with tea plantations, misty valleys, and waterfalls.",
        "attractions": ["Eravikulam National Park", "Mattupetty Dam", "Anamudi Peak", "Tea Museum"]
    },
    {
        "name": "Coorg", "state": "Karnataka", "avg_travel_cost": 2000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Nature",
        "best_season": "October to April", "description": "Known as the Scotland of India, rich in coffee plantations, lush forests, and wildlife.",
        "attractions": ["Abbey Falls", "Raja's Seat", "Dubare Elephant Camp", "Tala Kaveri"]
    },
    {
        "name": "Ooty", "state": "Tamil Nadu", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "Nature",
        "best_season": "October to June", "description": "Classic Nilgiri hill station with colonial charm, botanical gardens, and toy train ride.",
        "attractions": ["Ooty Lake", "Botanical Gardens", "Doddabetta Peak", "Nilgiri Mountain Railway"]
    },
    {
        "name": "Valley of Flowers", "state": "Uttarakhand", "avg_travel_cost": 4500.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 800.0, "rating": 4.9, "category": "Nature",
        "best_season": "July to September", "description": "A high-altitude Himalayan valley blooming with hundreds of endemic alpine flowers.",
        "attractions": ["Hemkund Sahib", "Ghangaria base camp", "Pushpawati River", "Valley Trek"]
    },
    {
        "name": "Wayanad", "state": "Kerala", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 350.0, "rating": 4.4, "category": "Nature",
        "best_season": "October to May", "description": "Spice plantations, pre-historic caves, mist-clad peaks, and wildlife sanctuaries.",
        "attractions": ["Edakkal Caves", "Banasura Sagar Dam", "Chembra Peak", "Pookode Lake"]
    },
    {
        "name": "Alleppey", "state": "Kerala", "avg_travel_cost": 3200.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 800.0, "rating": 4.6, "category": "Nature",
        "best_season": "September to March", "description": "Venice of the East, famous for houseboat cruises along lazy backwaters.",
        "attractions": ["Alappuzha Beach", "Vembanad Lake", "Pathiramanal Island", "Backwater Cruise"]
    },
    {
        "name": "Kodaikanal", "state": "Tamil Nadu", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2100.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 300.0, "rating": 4.5, "category": "Nature",
        "best_season": "September to May", "description": "The Gift of the Forest, centered around a man-made star-shaped lake.",
        "attractions": ["Kodaikanal Lake", "Coaker's Walk", "Pillar Rocks", "Bryant Park"]
    },
    {
        "name": "Mount Abu", "state": "Rajasthan", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 250.0, "rating": 4.2, "category": "Nature",
        "best_season": "October to March", "description": "The only hill station in Rajasthan, featuring beautiful Dilwara temples and Nakki Lake.",
        "attractions": ["Dilwara Temples", "Nakki Lake", "Guru Shikhar", "Sunset Point"]
    },
    {
        "name": "Araku Valley", "state": "Andhra Pradesh", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 300.0, "rating": 4.2, "category": "Nature",
        "best_season": "October to March", "description": "Scenic valley in Eastern Ghats famous for coffee plantations and tribal museums.",
        "attractions": ["Borra Caves", "Katiki Waterfalls", "Coffee Museum", "Padmapuram Gardens"]
    },
    {
        "name": "Lonavala", "state": "Maharashtra", "avg_travel_cost": 1000.0, "avg_hotel_cost": 2400.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "Nature",
        "best_season": "June to September", "description": "Western Ghats hill station blooming with waterfalls, fog, and dense green hills during monsoon.",
        "attractions": ["Bhushi Dam", "Tiger's Point", "Karla Caves", "Lohagad Fort"]
    },
    {
        "name": "Chikmagalur", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1900.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Nature",
        "best_season": "September to March", "description": "Coffee country with misty Mullayanagiri peaks, waterfalls, and plantation homestays.",
        "attractions": ["Mullayanagiri Peak", "Hebbe Falls", "Baba Budangiri", "Coffee Estate Tour"]
    },
    {
        "name": "Idukki", "state": "Kerala", "avg_travel_cost": 2800.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 450.0, "rating": 4.4, "category": "Nature",
        "best_season": "September to May", "description": "Arch dam vistas, spice gardens, and rolling green hills in Kerala's high ranges.",
        "attractions": ["Idukki Arch Dam", "Ramakkalmedu", "Hill View Park", "Spice Plantation Walk"]
    },
    {
        "name": "Kalimpong", "state": "West Bengal", "avg_travel_cost": 3200.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "Nature",
        "best_season": "March to May, September to December", "description": "Quiet Himalayan town with flower nurseries, monasteries, and Kanchenjunga viewpoints.",
        "attractions": ["Deolo Hill", "Morgan House", "Durpin Monastery", "Cactus Nursery"]
    },
    {
        "name": "Saputara", "state": "Gujarat", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 300.0, "rating": 4.1, "category": "Nature",
        "best_season": "October to February", "description": "Gujarat's only hill station with a lake, ropeway, tribal museums, and monsoon greenery.",
        "attractions": ["Saputara Lake", "Sunset Point", "Gira Falls", "Ropeway Ride"]
    },
    {
        "name": "Ziro Valley", "state": "Arunachal Pradesh", "avg_travel_cost": 5500.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 500.0, "rating": 4.6, "category": "Nature",
        "best_season": "March to October", "description": "UNESCO-listed Apatani cultural landscape of pine hills, rice fields, and music festivals.",
        "attractions": ["Talley Valley Wildlife Sanctuary", "Apatani Villages", "Ziro Music Festival Grounds", "Kile Pakho Ridge"]
    },

    # ADVENTURE (15)
    {
        "name": "Rishikesh", "state": "Uttarakhand", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 1500.0, "rating": 4.6, "category": "Adventure",
        "best_season": "September to June", "description": "Adventure capital, legendary for white-water rafting, bungee jumping, and yoga.",
        "attractions": ["Laxman Jhula", "Triveni Ghat", "Shivpuri Rafting Base", "Beatles Ashram"]
    },
    {
        "name": "Manali", "state": "Himachal Pradesh", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1200.0, "rating": 4.5, "category": "Adventure",
        "best_season": "October to June", "description": "Snowy peak views, paragliding, zorbing, and skiing in Solang Valley.",
        "attractions": ["Solang Valley", "Hadimba Temple", "Rohtang Pass", "Jogini Waterfalls"]
    },
    {
        "name": "Leh Ladakh", "state": "Ladakh", "avg_travel_cost": 7000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 2500.0, "rating": 4.9, "category": "Adventure",
        "best_season": "June to September", "description": "High-altitude desert wonderland featuring pristine lakes and motorable mountain passes.",
        "attractions": ["Pangong Tso", "Nubra Valley", "Khardung La", "Magnetic Hill"]
    },
    {
        "name": "Bir Billing", "state": "Himachal Pradesh", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1300.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 2500.0, "rating": 4.6, "category": "Adventure",
        "best_season": "October to June", "description": "Asia's premier paragliding destination, dotted with beautiful Buddhist monasteries.",
        "attractions": ["Billing Takeoff Point", "Bir Landing Site", "Sherab Ling Monastery", "Deer Park Institute"]
    },
    {
        "name": "Auli", "state": "Uttarakhand", "avg_travel_cost": 4000.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.7, "category": "Adventure",
        "best_season": "December to March", "description": "India's premier ski resort surrounded by oak forests and majestic peaks like Nanda Devi.",
        "attractions": ["Auli Ropeway", "Auli Artificial Lake", "Gurso Bugyal", "Joshimath"]
    },
    {
        "name": "Spiti Valley", "state": "Himachal Pradesh", "avg_travel_cost": 5000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 1200.0, "rating": 4.8, "category": "Adventure",
        "best_season": "June to September", "description": "Cold desert valley, home to medieval monasteries, high villages, and trekking trails.",
        "attractions": ["Key Monastery", "Chandratal Lake", "Kaza", "Hikkim Post Office"]
    },
    {
        "name": "Gulmarg", "state": "Jammu & Kashmir", "avg_travel_cost": 5000.0, "avg_hotel_cost": 4000.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 2000.0, "rating": 4.8, "category": "Adventure",
        "best_season": "December to April", "description": "Famed for its Gondola ride (highest cable car) and deep powder winter skiing.",
        "attractions": ["Gulmarg Gondola", "Apharwat Peak", "Strawberry Valley", "Gulmarg Golf Course"]
    },
    {
        "name": "Jim Corbett", "state": "Uttarakhand", "avg_travel_cost": 1800.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 1500.0, "rating": 4.4, "category": "Adventure",
        "best_season": "November to May", "description": "India's oldest national park, legendary for Royal Bengal Tiger safaris and river rafting.",
        "attractions": ["Dhikala Zone", "Bijrani Zone", "Corbett Falls", "Kosi River"]
    },
    {
        "name": "Tawang", "state": "Arunachal Pradesh", "avg_travel_cost": 6000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 1000.0, "rating": 4.7, "category": "Adventure",
        "best_season": "March to June", "description": "High-altitude town with ancient monasteries, high lakes, and snowy passes.",
        "attractions": ["Tawang Monastery", "Sela Pass", "Nuranang Falls", "Madhuri Lake"]
    },
    {
        "name": "Yumthang Valley", "state": "Sikkim", "avg_travel_cost": 5000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1200.0, "rating": 4.7, "category": "Adventure",
        "best_season": "April to June", "description": "Valley of Flowers of the East, surrounded by snow peaks and natural hot springs.",
        "attractions": ["Yumesamdong (Zero Point)", "Lachung", "Hot Springs", "Shingba Rhododendron Sanctuary"]
    },
    {
        "name": "Kasol", "state": "Himachal Pradesh", "avg_travel_cost": 2400.0, "avg_hotel_cost": 1100.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 1400.0, "rating": 4.5, "category": "Adventure",
        "best_season": "March to June", "description": "Parvati Valley base for treks, riverside camps, and trails to Kheerganga and Malana.",
        "attractions": ["Parvati River", "Kheerganga Trek", "Manikaran Sahib", "Chalal Village Trail"]
    },
    {
        "name": "Dandeli", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 1800.0, "rating": 4.4, "category": "Adventure",
        "best_season": "October to May", "description": "White-water rafting on the Kali River, jungle safaris, and canopy walks in dense forests.",
        "attractions": ["Kali River Rafting", "Dandeli Wildlife Sanctuary", "Syntheri Rocks", "Kayaking Point"]
    },
    {
        "name": "Chadar Trek", "state": "Ladakh", "avg_travel_cost": 8000.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 3500.0, "rating": 4.9, "category": "Adventure",
        "best_season": "January to February", "description": "Legendary winter trek walking on the frozen Zanskar River through dramatic ice canyons.",
        "attractions": ["Frozen Zanskar River", "Nerak Waterfall", "Tilat Sumdo Camp", "Tsomo Paldar"]
    },
    {
        "name": "Meghalaya Caves", "state": "Meghalaya", "avg_travel_cost": 4500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 2000.0, "rating": 4.7, "category": "Adventure",
        "best_season": "October to May", "description": "Caving expeditions through limestone chambers, living root bridges, and waterfall hikes.",
        "attractions": ["Mawsmai Cave", "Double Decker Root Bridge", "Nohkalikai Falls", "Dawki River"]
    },
    {
        "name": "Zanskar Valley", "state": "Ladakh", "avg_travel_cost": 6500.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 2200.0, "rating": 4.8, "category": "Adventure",
        "best_season": "June to September", "description": "Remote Buddhist valley of dramatic gorges, ancient monasteries, and high-altitude rafting.",
        "attractions": ["Padum", "Phugtal Monastery", "Zanskar River Rafting", "Drang Drung Glacier View"]
    },

    # RELIGIOUS (15)
    {
        "name": "Varanasi", "state": "Uttar Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 200.0, "rating": 4.7, "category": "Religious",
        "best_season": "October to March", "description": "One of the world's oldest continually inhabited cities, spiritual capital of India.",
        "attractions": ["Kashi Vishwanath Temple", "Dashashwamedh Ghat Aarti", "Sarnath", "Assi Ghat"]
    },
    {
        "name": "Amritsar", "state": "Punjab", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 150.0, "rating": 4.8, "category": "Religious",
        "best_season": "October to March", "description": "Home of the sacred Golden Temple and delicious Punjabi street cuisine.",
        "attractions": ["Harmandir Sahib (Golden Temple)", "Wagah Border", "Jallianwala Bagh", "Partition Museum"]
    },
    {
        "name": "Tirupati", "state": "Andhra Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.6, "category": "Religious",
        "best_season": "September to March", "description": "One of the most visited pilgrimage sites in the world, dedicated to Lord Venkateswara.",
        "attractions": ["Tirumala Temple", "Kapila Theertham", "Padmavathi Temple", "Srivari Mettu"]
    },
    {
        "name": "Jagannath Puri", "state": "Odisha", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 150.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to February", "description": "A Char Dham pilgrimage destination, famous for the annual Rath Yatra festival.",
        "attractions": ["Shree Jagannath Temple", "Gundicha Temple", "Puri Beach", "Narendra Tank"]
    },
    {
        "name": "Madurai", "state": "Tamil Nadu", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Ancient city built around the glorious temple complex of Meenakshi Amman.",
        "attractions": ["Meenakshi Amman Temple", "Thirumalai Nayakkar Palace", "Koodal Azhagar Temple", "Gandhi Museum"]
    },
    {
        "name": "Kedarnath", "state": "Uttarakhand", "avg_travel_cost": 4500.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 600.0, "rating": 4.9, "category": "Religious",
        "best_season": "May to June, September to October", "description": "Sacred shrine of Lord Shiva located at 11,000 feet amidst Himalayan snow glaciers.",
        "attractions": ["Kedarnath Temple", "Bhairav Temple", "Chorabari Lake", "Gaurikund"]
    },
    {
        "name": "Haridwar", "state": "Uttarakhand", "avg_travel_cost": 1200.0, "avg_hotel_cost": 1100.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 150.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Sacred place where the River Ganges leaves the mountains to enter the plains.",
        "attractions": ["Har Ki Pauri", "Mansa Devi Temple", "Chandi Devi Temple", "Ganga Aarti"]
    },
    {
        "name": "Rameshwaram", "state": "Tamil Nadu", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 250.0, "rating": 4.6, "category": "Religious",
        "best_season": "October to March", "description": "Island town connected to mainland India by the historic Pamban bridge, a sacred spot.",
        "attractions": ["Ramanathaswamy Temple", "Agni Theertham", "Dhanushkodi ghost town", "Pamban Bridge"]
    },
    {
        "name": "Dwarka", "state": "Gujarat", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.5, "category": "Religious",
        "best_season": "October to March", "description": "Ancient capital of Lord Krishna's kingdom, sitting at the tip of the Kathiawar peninsula.",
        "attractions": ["Dwarkadhish Temple", "Bet Dwarka", "Nageshwar Jyotirlinga", "Rukmini Devi Temple"]
    },
    {
        "name": "Shirdi", "state": "Maharashtra", "avg_travel_cost": 1200.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 150.0, "rating": 4.4, "category": "Religious",
        "best_season": "October to March", "description": "The holy home of the 19th-century spiritual master Sai Baba.",
        "attractions": ["Sai Baba Samadhi Mandir", "Dwarkamai", "Chavadi", "Dixit Wada Museum"]
    },
    {
        "name": "Ajmer Sharif", "state": "Rajasthan", "avg_travel_cost": 1600.0, "avg_hotel_cost": 1300.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 180.0, "rating": 4.6, "category": "Religious",
        "best_season": "October to March", "description": "Sufi shrine of Khwaja Moinuddin Chishti drawing pilgrims from across South Asia.",
        "attractions": ["Dargah Sharif", "Ana Sagar Lake", "Adhai Din Ka Jhonpra", "Taragarh Fort"]
    },
    {
        "name": "Badrinath", "state": "Uttarakhand", "avg_travel_cost": 4800.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 550.0, "rating": 4.8, "category": "Religious",
        "best_season": "May to June, September to October", "description": "Char Dham temple of Lord Vishnu set against the Neelkanth peak in the Garhwal Himalayas.",
        "attractions": ["Badrinath Temple", "Tapt Kund", "Mana Village", "Vasudhara Falls"]
    },
    {
        "name": "Bodh Gaya", "state": "Bihar", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 200.0, "rating": 4.7, "category": "Religious",
        "best_season": "October to March", "description": "Where Buddha attained enlightenment beneath the Bodhi tree, a UNESCO World Heritage site.",
        "attractions": ["Mahabodhi Temple", "Bodhi Tree", "Great Buddha Statue", "Thai Monastery"]
    },
    {
        "name": "Somnath", "state": "Gujarat", "avg_travel_cost": 2400.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.6, "category": "Religious",
        "best_season": "October to March", "description": "First among the twelve Jyotirlinga shrines, rebuilt on the shores of the Arabian Sea.",
        "attractions": ["Somnath Temple", "Triveni Sangam", "Bhalka Tirth", "Somnath Beach"]
    },
    {
        "name": "Palani", "state": "Tamil Nadu", "avg_travel_cost": 1400.0, "avg_hotel_cost": 1100.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 180.0, "rating": 4.4, "category": "Religious",
        "best_season": "October to March", "description": "Hilltop Murugan temple reached by ropeway, one of Tamil Nadu's most visited shrines.",
        "attractions": ["Palani Murugan Temple", "Temple Ropeway", "Kongu Nadu Viewpoint", "Idumban Shrine"]
    },

    # CITY EXPLORATION (15)
    {
        "name": "Mumbai", "state": "Maharashtra", "avg_travel_cost": 1500.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 900.0, "avg_activity_cost": 400.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "October to March", "description": "The City of Dreams, featuring colonial monuments, beaches, and high-energy local life.",
        "attractions": ["Gateway of India", "Marine Drive", "Elephanta Caves", "Colaba Causeway"]
    },
    {
        "name": "Delhi", "state": "Delhi", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "India's capital, where ancient history meets bustling modern shopping hubs.",
        "attractions": ["Red Fort", "Qutub Minar", "India Gate", "Chandni Chowk markets"]
    },
    {
        "name": "Bengaluru", "state": "Karnataka", "avg_travel_cost": 2000.0, "avg_hotel_cost": 2600.0,
        "avg_food_cost": 850.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "The Garden City and IT Hub, famous for its craft breweries, parks, and startup vibe.",
        "attractions": ["Lalbagh Botanical Garden", "Bangalore Palace", "Cubbon Park", "Indiranagar cafes"]
    },
    {
        "name": "Hyderabad", "state": "Telangana", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "October to March", "description": "City of Pearls, famous for its rich history, palaces, and world-class Biryani.",
        "attractions": ["Charminar", "Golconda Fort", "Chowmahalla Palace", "Ramoji Film City"]
    },
    {
        "name": "Kolkata", "state": "West Bengal", "avg_travel_cost": 2500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 250.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "Cultural capital, boasting grand colonial architecture and traditional sweet shops.",
        "attractions": ["Victoria Memorial", "Howrah Bridge", "Dakshineswar Temple", "Park Street"]
    },
    {
        "name": "Chandigarh", "state": "Punjab & Haryana", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 250.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "India's cleanest and most organized planned city, conceptualized by Le Corbusier.",
        "attractions": ["Rock Garden", "Sukhna Lake", "Rose Garden", "Sector 17 Market"]
    },
    {
        "name": "Pune", "state": "Maharashtra", "avg_travel_cost": 1000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 300.0, "rating": 4.2, "category": "City Exploration",
        "best_season": "October to March", "description": "The Oxford of the East, presenting historical forts, academic vibes, and hill surrounds.",
        "attractions": ["Shaniwar Wada", "Aga Khan Palace", "Sinhagad Fort", "Koregaon Park"]
    },
    {
        "name": "Kochi", "state": "Kerala", "avg_travel_cost": 3200.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "October to March", "description": "Historic spice port with Dutch, Portuguese, and British colonial influences.",
        "attractions": ["Fort Kochi Chinese Nets", "Mattancherry Palace", "Jewish Synagogue", "Marine Drive"]
    },
    {
        "name": "Ahmedabad", "state": "Gujarat", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 200.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "A UNESCO heritage city showcasing historic stepwells and Mahatma Gandhi's Ashram.",
        "attractions": ["Sabarmati Ashram", "Adalaj Stepwell", "Kankaria Lake", "Teen Darwaza"]
    },
    {
        "name": "Chennai", "state": "Tamil Nadu", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 250.0, "rating": 4.2, "category": "City Exploration",
        "best_season": "October to March", "description": "Gateway to the South, famous for Marina Beach, temples, and rich Carnatic heritage.",
        "attractions": ["Marina Beach", "Kapaleeshwarar Temple", "Santhome Cathedral", "Fort St. George"]
    },
    {
        "name": "Jaipur", "state": "Rajasthan", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2400.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "The Pink City of grand forts, royal palaces, bazaars, and Rajasthani cuisine.",
        "attractions": ["Amber Fort", "Hawa Mahal", "City Palace", "Johari Bazaar"]
    },
    {
        "name": "Lucknow", "state": "Uttar Pradesh", "avg_travel_cost": 1600.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 250.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "Nawabi heritage city famed for kebabs, Awadhi cuisine, and Mughal-era architecture.",
        "attractions": ["Bara Imambara", "Chota Imambara", "Rumi Darwaza", "Hazratganj"]
    },
    {
        "name": "Indore", "state": "Madhya Pradesh", "avg_travel_cost": 1400.0, "avg_hotel_cost": 1900.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 220.0, "rating": 4.2, "category": "City Exploration",
        "best_season": "October to March", "description": "Central India's food capital with street snacks, Rajwada Palace, and lively night markets.",
        "attractions": ["Rajwada Palace", "Sarafa Bazaar", "Lal Bagh Palace", "Kanch Mandir"]
    },
    {
        "name": "Guwahati", "state": "Assam", "avg_travel_cost": 2800.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to April", "description": "Gateway to Northeast India with river cruises, Kamakhya Temple, and tea-country access.",
        "attractions": ["Kamakhya Temple", "Umananda Island", "Brahmaputra River Cruise", "Assam State Museum"]
    },
    {
        "name": "Mysuru", "state": "Karnataka", "avg_travel_cost": 1600.0, "avg_hotel_cost": 2100.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 280.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "October to March", "description": "Cultural city of illuminated palaces, silk markets, yoga traditions, and Dasara festivities.",
        "attractions": ["Mysore Palace", "Chamundi Hills", "Devaraja Market", "Brindavan Gardens"]
    },

    # ROMANTIC (15)
    {
        "name": "Srinagar", "state": "Jammu & Kashmir", "avg_travel_cost": 4500.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 600.0, "rating": 4.8, "category": "Romantic",
        "best_season": "April to October", "description": "Paradise on Earth, famous for Shikara rides on Dal Lake and vibrant Mughal gardens.",
        "attractions": ["Dal Lake", "Shalimar Bagh", "Nishat Bagh", "Shikara Ride"]
    },
    {
        "name": "Udaipur", "state": "Rajasthan", "avg_travel_cost": 2200.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 450.0, "rating": 4.7, "category": "Romantic",
        "best_season": "September to March", "description": "The City of Lakes and Venice of the East, boasting gorgeous floating palaces.",
        "attractions": ["City Palace", "Lake Pichola Boat Ride", "Jag Mandir", "Sajjangarh Palace"]
    },
    {
        "name": "Gulmarg Valley", "state": "Jammu & Kashmir", "avg_travel_cost": 5000.0, "avg_hotel_cost": 4500.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 1500.0, "rating": 4.8, "category": "Romantic",
        "best_season": "December to April", "description": "Ski resort that transforms into a meadow of flowers in spring, perfect for couples.",
        "attractions": ["Gulmarg Meadows", "St. Mary's Church", "Apharwat Peak", "Alpathar Lake"]
    },
    {
        "name": "Manali Couple Getaway", "state": "Himachal Pradesh", "avg_travel_cost": 2500.0, "avg_hotel_cost": 2400.0,
        "avg_food_cost": 750.0, "avg_activity_cost": 800.0, "rating": 4.6, "category": "Romantic",
        "best_season": "October to June", "description": "Misty cedar forests, river side dining, and cozy wooden mountain cottages.",
        "attractions": ["Old Manali cafes", "Solang Valley", "Van Vihar", "Jogini Falls"]
    },
    {
        "name": "Shimla", "state": "Himachal Pradesh", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "Romantic",
        "best_season": "October to June", "description": "The summer capital of British India, known for colonial architecture and snowy strolls.",
        "attractions": ["The Ridge", "Mall Road", "Jakhoo Temple", "Kalka-Shimla Toy Train"]
    },
    {
        "name": "Ooty Honeymoon special", "state": "Tamil Nadu", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Romantic",
        "best_season": "October to June", "description": "Emerald-green tea garden hills, rose gardens, and private lake boating.",
        "attractions": ["Pykara Lake & Falls", "Botanical Gardens", "Rose Garden", "Avalanche Lake"]
    },
    {
        "name": "Darjeeling", "state": "West Bengal", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 300.0, "rating": 4.6, "category": "Romantic",
        "best_season": "October to May", "description": "Stunning views of Mount Kanchenjunga, tea fields, and historic steam railways.",
        "attractions": ["Tiger Hill Sunrise", "Batasia Loop", "Ghoom Monastery", "Darjeeling Ropeway"]
    },
    {
        "name": "Munnar Retreat", "state": "Kerala", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2600.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 400.0, "rating": 4.6, "category": "Romantic",
        "best_season": "September to May", "description": "Misty tea estates, serene lakes, and high-altitude luxury resorts for couples.",
        "attractions": ["Echo Point", "Kundala Lake", "Eravikulam Park", "Attukad Waterfalls"]
    },
    {
        "name": "Nainital", "state": "Uttarakhand", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "Romantic",
        "best_season": "September to June", "description": "A beautiful lake resort town set in a valley surrounding a pear-shaped volcanic lake.",
        "attractions": ["Naini Lake boating", "Mall Road", "Snow View Point", "Tiffin Top"]
    },
    {
        "name": "Alleppey Houseboat", "state": "Kerala", "avg_travel_cost": 3200.0, "avg_hotel_cost": 4500.0,
        "avg_food_cost": 1000.0, "avg_activity_cost": 1000.0, "rating": 4.7, "category": "Romantic",
        "best_season": "September to March", "description": "Luxury private wooden houseboats cruising along palm-fringed Kerala backwaters.",
        "attractions": ["Vembanad Lake", "Kuttanad paddy fields", "Punnamada Lake", "Alappuzha Beach"]
    },
    {
        "name": "Kumarakom", "state": "Kerala", "avg_travel_cost": 3000.0, "avg_hotel_cost": 3800.0,
        "avg_food_cost": 900.0, "avg_activity_cost": 700.0, "rating": 4.6, "category": "Romantic",
        "best_season": "September to March", "description": "Lakeside resorts on Vembanad with bird sanctuaries, sunset cruises, and Ayurveda spas.",
        "attractions": ["Kumarakom Bird Sanctuary", "Vembanad Lake Cruise", "Pathiramanal Island", "Ayurveda Spa"]
    },
    {
        "name": "Kasauli", "state": "Himachal Pradesh", "avg_travel_cost": 2000.0, "avg_hotel_cost": 2100.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "Romantic",
        "best_season": "March to June, September to November", "description": "Colonial-era hill town with misty walks, heritage churches, and quiet forest trails.",
        "attractions": ["Monkey Point", "Christ Church", "Gilbert Trail", "Sunset Point"]
    },
    {
        "name": "Cherrapunji", "state": "Meghalaya", "avg_travel_cost": 4200.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 500.0, "rating": 4.5, "category": "Romantic",
        "best_season": "October to May", "description": "Rain-soaked cliffs, living root bridges, and misty waterfalls in the wettest place on Earth.",
        "attractions": ["Nohkalikai Falls", "Double Decker Root Bridge", "Mawsmai Cave", "Seven Sisters Falls"]
    },
    {
        "name": "Thekkady", "state": "Kerala", "avg_travel_cost": 2800.0, "avg_hotel_cost": 2400.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 600.0, "rating": 4.5, "category": "Romantic",
        "best_season": "September to May", "description": "Periyar wildlife sanctuary surrounds spice plantations, lake cruises, and jungle lodges.",
        "attractions": ["Periyar Lake Cruise", "Spice Plantation Tour", "Bamboo Rafting", "Elephant Junction"]
    },
    {
        "name": "Mahabaleshwar", "state": "Maharashtra", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2300.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 350.0, "rating": 4.4, "category": "Romantic",
        "best_season": "October to June", "description": "Strawberry farms, misty viewpoints, and colonial-era hill cottages in the Western Ghats.",
        "attractions": ["Wilson Point", "Mapro Garden", "Venna Lake", "Arthur's Seat"]
    },

    # FAMILY (10)
    {
        "name": "Mahabaleshwar Family Getaway", "state": "Maharashtra", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 400.0, "rating": 4.4, "category": "Family",
        "best_season": "October to June", "description": "Kid-friendly hill station with boating, strawberry farms, and easy nature walks.",
        "attractions": ["Venna Lake Boating", "Mapro Garden", "Elephant's Head Point", "Panchgani Table Land"]
    },
    {
        "name": "Ooty Family Escape", "state": "Tamil Nadu", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2100.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "Family",
        "best_season": "October to June", "description": "Toy train rides, botanical gardens, and gentle lake activities for all ages.",
        "attractions": ["Ooty Lake", "Botanical Gardens", "Nilgiri Mountain Railway", "Doddabetta Peak"]
    },
    {
        "name": "Lonavala Family Weekend", "state": "Maharashtra", "avg_travel_cost": 1000.0, "avg_hotel_cost": 2300.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 400.0, "rating": 4.3, "category": "Family",
        "best_season": "June to September", "description": "Short-drive hill escape with dams, viewpoints, and chikki shops perfect for weekend trips.",
        "attractions": ["Bhushi Dam", "Tiger's Point", "Imagicaa Theme Park", "Karla Caves"]
    },
    {
        "name": "Mussoorie Family Hills", "state": "Uttarakhand", "avg_travel_cost": 2000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "Family",
        "best_season": "April to June, September to November", "description": "Queen of Hills with cable car rides, mall road strolls, and Kempty Falls picnics.",
        "attractions": ["Gun Hill Cable Car", "Kempty Falls", "Mall Road", "Company Garden"]
    },
    {
        "name": "Jaipur Heritage Family", "state": "Rajasthan", "avg_travel_cost": 1800.0, "avg_hotel_cost": 2300.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Family",
        "best_season": "October to March", "description": "Palaces, forts, and colorful bazaars offering engaging history lessons for children.",
        "attractions": ["Amber Fort", "City Palace", "Jantar Mantar", "Chokhi Dhani Village"]
    },
    {
        "name": "South Goa Family Resort", "state": "Goa", "avg_travel_cost": 3000.0, "avg_hotel_cost": 3200.0,
        "avg_food_cost": 900.0, "avg_activity_cost": 500.0, "rating": 4.5, "category": "Family",
        "best_season": "November to February", "description": "Calm beaches, resort pools, and dolphin-spotting cruises ideal for family holidays.",
        "attractions": ["Palolem Beach", "Cabo de Rama Fort", "Dolphin Cruise", "Colva Beach"]
    },
    {
        "name": "Mysore Family Circuit", "state": "Karnataka", "avg_travel_cost": 1600.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "Family",
        "best_season": "October to March", "description": "Illuminated palace visits, zoo outings, and garden fountain shows for relaxed family touring.",
        "attractions": ["Mysore Palace", "Sri Chamarajendra Zoo", "Brindavan Gardens", "Chamundi Hills"]
    },
    {
        "name": "Darjeeling Family Tour", "state": "West Bengal", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2100.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "Family",
        "best_season": "October to May", "description": "Toy train joyrides, tea garden visits, and sunrise viewpoints the whole family can enjoy.",
        "attractions": ["Darjeeling Himalayan Railway", "Tiger Hill", "Padmaja Naidu Zoo", "Batasia Loop"]
    },
    {
        "name": "Kerala Family Backwaters", "state": "Kerala", "avg_travel_cost": 3000.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 600.0, "rating": 4.6, "category": "Family",
        "best_season": "September to March", "description": "Houseboat stays, village canoe rides, and Kathakali shows on gentle backwater routes.",
        "attractions": ["Alleppey Houseboat", "Kumarakom Bird Sanctuary", "Village Canoe Ride", "Kathakali Centre"]
    },
    {
        "name": "Mount Abu Family Parks", "state": "Rajasthan", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 300.0, "rating": 4.2, "category": "Family",
        "best_season": "October to March", "description": "Rajasthan's cool hill retreat with lake boating, wildlife sanctuary, and sunset points.",
        "attractions": ["Nakki Lake", "Sunset Point", "Mount Abu Wildlife Sanctuary", "Achalgarh Fort"]
    },

    # SOLO (10)
    {
        "name": "Hampi", "state": "Karnataka", "avg_travel_cost": 1800.0, "avg_hotel_cost": 900.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 250.0, "rating": 4.7, "category": "Solo",
        "best_season": "October to March", "description": "UNESCO boulder-strewn ruins of the Vijayanagara Empire, perfect for solo exploration on a moped.",
        "attractions": ["Virupaksha Temple", "Vittala Temple", "Matanga Hill Sunrise", "Hemakuta Hill"]
    },
    {
        "name": "Mcleodganj", "state": "Himachal Pradesh", "avg_travel_cost": 2400.0, "avg_hotel_cost": 1000.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 600.0, "rating": 4.6, "category": "Solo",
        "best_season": "March to June", "description": "Tibetan culture hub with monasteries, trekking trails, and a thriving solo backpacker scene.",
        "attractions": ["Tsuglagkhang Complex", "Bhagsu Falls", "Triund Trek", "Dal Lake Mcleodganj"]
    },
    {
        "name": "Pushkar", "state": "Rajasthan", "avg_travel_cost": 1600.0, "avg_hotel_cost": 800.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 200.0, "rating": 4.5, "category": "Solo",
        "best_season": "October to March", "description": "Sacred lake town with rooftop cafes, camel fairs, and a relaxed solo-traveler atmosphere.",
        "attractions": ["Pushkar Lake", "Brahma Temple", "Savitri Temple Hike", "Pushkar Bazaar"]
    },
    {
        "name": "Vashisht", "state": "Himachal Pradesh", "avg_travel_cost": 2200.0, "avg_hotel_cost": 900.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 500.0, "rating": 4.4, "category": "Solo",
        "best_season": "March to June", "description": "Hot springs village above Manali with budget guesthouses and trails into pine forests.",
        "attractions": ["Vashisht Hot Springs", "Jogini Waterfall Trek", "Old Vashisht Temple", "Forest Trail"]
    },
    {
        "name": "Kasol Solo Trail", "state": "Himachal Pradesh", "avg_travel_cost": 2400.0, "avg_hotel_cost": 1000.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 800.0, "rating": 4.5, "category": "Solo",
        "best_season": "March to June", "description": "Parvati Valley backpacker hub with riverside cafes, treks, and a strong solo traveler community.",
        "attractions": ["Parvati River Walk", "Chalal Village", "Kheerganga Trek", "Manikaran Hot Springs"]
    },
    {
        "name": "Pondicherry Solo", "state": "Tamil Nadu", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 250.0, "rating": 4.4, "category": "Solo",
        "best_season": "October to March", "description": "French Quarter cafes, beach promenades, and Auroville day trips ideal for independent travelers.",
        "attractions": ["French Quarter", "Promenade Beach", "Auroville", "Paradise Beach"]
    },
    {
        "name": "Jaipur Solo Explorer", "state": "Rajasthan", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 300.0, "rating": 4.4, "category": "Solo",
        "best_season": "October to March", "description": "Walkable heritage quarters, rooftop restaurants, and affordable hostels for solo city explorers.",
        "attractions": ["Hawa Mahal", "Nahargarh Fort Sunset", "Johari Bazaar", "Patrika Gate"]
    },
    {
        "name": "Gokarna Solo Beach", "state": "Karnataka", "avg_travel_cost": 2000.0, "avg_hotel_cost": 800.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 200.0, "rating": 4.5, "category": "Solo",
        "best_season": "October to March", "description": "Budget beach shacks, cliff trails between beaches, and a laid-back solo surf-and-trek vibe.",
        "attractions": ["Om Beach", "Kudle Beach", "Beach Cliff Trail", "Half Moon Beach Trek"]
    },
    {
        "name": "Ziro Solo", "state": "Arunachal Pradesh", "avg_travel_cost": 5500.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 400.0, "rating": 4.6, "category": "Solo",
        "best_season": "March to October", "description": "Offbeat pine hills and Apatani culture attracting independent travelers and festival goers.",
        "attractions": ["Talley Valley", "Apatani Village Walk", "Ziro Pine Grove", "Kile Pakho Viewpoint"]
    },
    {
        "name": "Varkala Cliff Solo", "state": "Kerala", "avg_travel_cost": 3500.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "Solo",
        "best_season": "October to March", "description": "Cliff-top hostels, yoga retreats, and surf lessons on Kerala's most solo-friendly beach strip.",
        "attractions": ["Varkala Cliff", "Papanasam Beach", "Janardhana Temple", "Surf School"]
    },

    # ADDITIONAL BEACH
    {
        "name": "Mandarmani", "state": "West Bengal", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 200.0, "rating": 4.0, "category": "Beach",
        "best_season": "November to March", "description": "Eastern India's longest motor-able beach, popular for seafood and peaceful evening strolls.",
        "attractions": ["Mandarmani Beach", "Digha Beach", "Red Crab Colony", "Shankarpur Fishing Port"]
    },
    {
        "name": "Digha", "state": "West Bengal", "avg_travel_cost": 1600.0, "avg_hotel_cost": 1300.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 200.0, "rating": 3.9, "category": "Beach",
        "best_season": "October to March", "description": "Classic budget beach resort with broad sandy shores and the historic Marine Aquarium.",
        "attractions": ["New Digha Beach", "Old Digha Beach", "Marine Aquarium", "Amrabati Park"]
    },
    {
        "name": "Rameswaram Coast", "state": "Tamil Nadu", "avg_travel_cost": 2500.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 300.0, "rating": 4.3, "category": "Beach",
        "best_season": "October to April", "description": "Sacred temple town blending tranquil beaches, coral reefs, and snorkelling trips to Adam's Bridge.",
        "attractions": ["Dhanushkodi beach ruins", "Ariyaman Beach", "Pamban Bridge view", "Agni Theertham"]
    },
    {
        "name": "Murudeshwar", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 500.0, "rating": 4.4, "category": "Beach",
        "best_season": "October to March", "description": "Dramatic sea-cliff temple site with the world's second-tallest Shiva statue and excellent diving.",
        "attractions": ["Murudeshwar Temple", "Murudeshwar Beach", "Scuba Diving Site", "R.N. Shetty Tower"]
    },
    {
        "name": "Vizag Beach", "state": "Andhra Pradesh", "avg_travel_cost": 2200.0, "avg_hotel_cost": 1900.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.3, "category": "Beach",
        "best_season": "October to February", "description": "City of destiny with picturesque RK Beach, submarine museum, and hilltop viewpoints.",
        "attractions": ["RK Beach", "Kailasagiri", "INS Kurusura Submarine Museum", "Rushikonda Beach"]
    },
    {
        "name": "Marari Beach", "state": "Kerala", "avg_travel_cost": 3500.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Beach",
        "best_season": "November to March", "description": "Uncrowded fishing village beach with coconut groves, hammocks, and organic resort retreats.",
        "attractions": ["Marari Beach", "Fishermen Village Walk", "Kettuvallam Cruise", "Hammock Time"]
    },

    # ADDITIONAL NATURE
    {
        "name": "Chopta", "state": "Uttarakhand", "avg_travel_cost": 3800.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 700.0, "rating": 4.7, "category": "Nature",
        "best_season": "April to November", "description": "Mini Switzerland of India, a high meadow gateway to Tungnath (highest Shiva temple) and Chandrashila.",
        "attractions": ["Chandrashila Summit", "Tungnath Temple", "Deoria Tal", "Rohini Bugyal"]
    },
    {
        "name": "Dzukou Valley", "state": "Nagaland", "avg_travel_cost": 5000.0, "avg_hotel_cost": 800.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 900.0, "rating": 4.8, "category": "Nature",
        "best_season": "June to September", "description": "Extraordinary Naga highland valley carpeted with rare lilies and visited by very few tourists.",
        "attractions": ["Dzukou Valley Trek", "Japfu Peak", "Seasonal Lily Blooms", "Viswema Village Trail"]
    },
    {
        "name": "Kausani", "state": "Uttarakhand", "avg_travel_cost": 3200.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "Nature",
        "best_season": "March to June, September to November", "description": "Himalayan panorama viewpoint where Nanda Devi, Trishul, and Panchachuli peaks are visible.",
        "attractions": ["Anasakti Ashram", "Someshwar Valley", "Rudradhari Falls", "Binsar Wildlife Sanctuary"]
    },
    {
        "name": "Panchmarhi", "state": "Madhya Pradesh", "avg_travel_cost": 2400.0, "avg_hotel_cost": 1700.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 400.0, "rating": 4.3, "category": "Nature",
        "best_season": "October to June", "description": "MP's only hill station in Satpura Range, packed with waterfalls, ancient caves, and dense forests.",
        "attractions": ["Bee Falls", "Pandava Caves", "Priyadarshini Point", "Satpura National Park"]
    },
    {
        "name": "Majuli Island", "state": "Assam", "avg_travel_cost": 3500.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Nature",
        "best_season": "October to March", "description": "World's largest river island, home to Vaishnavite monasteries, mask-making, and birdwatching.",
        "attractions": ["Kamalabari Satra", "Auniati Satra", "Migjur Pahar", "Birdwatching Wetlands"]
    },
    {
        "name": "Nubra Valley", "state": "Ladakh", "avg_travel_cost": 7500.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1500.0, "rating": 4.8, "category": "Nature",
        "best_season": "June to September", "description": "Cold desert valley with Bactrian camels, sand dunes of Hunder, and ancient Diskit Monastery.",
        "attractions": ["Hunder Sand Dunes", "Diskit Monastery", "Bactrian Camel Safari", "Shyok River View"]
    },
    {
        "name": "Sattal", "state": "Uttarakhand", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 300.0, "rating": 4.2, "category": "Nature",
        "best_season": "March to June", "description": "Seven interconnected lakes amid oak and rhododendron forests, paradise for birdwatchers.",
        "attractions": ["Sattal Lake", "Bhimtal Lake", "Naukuchiatal", "Butterfly Research Centre"]
    },

    # ADDITIONAL ADVENTURE
    {
        "name": "Munsiyari", "state": "Uttarakhand", "avg_travel_cost": 4000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 1200.0, "rating": 4.7, "category": "Adventure",
        "best_season": "May to October", "description": "Base camp for Milam and Ralam glaciers, offering sheer Himalayan views and cultural immersions.",
        "attractions": ["Birthi Falls", "Milam Glacier Trek", "Khaliya Top", "Nanda Devi Temple"]
    },
    {
        "name": "Mechuka", "state": "Arunachal Pradesh", "avg_travel_cost": 7000.0, "avg_hotel_cost": 1300.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 1000.0, "rating": 4.8, "category": "Adventure",
        "best_season": "March to October", "description": "Isolated high-altitude frontier valley with ancient Samten Yongcha Monastery and Tsipo River views.",
        "attractions": ["Samten Yongcha Monastery", "Tsipo River Bridge", "Sigin Lake", "Mechuka Adventure Festival"]
    },
    {
        "name": "Sandakphu Trek", "state": "West Bengal", "avg_travel_cost": 4000.0, "avg_hotel_cost": 900.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 1500.0, "rating": 4.8, "category": "Adventure",
        "best_season": "April to May, October to December", "description": "Highest point of West Bengal offering views of four 8000-m peaks including Everest and Kanchenjunga.",
        "attractions": ["Sandakphu Peak", "Phalut", "Gurdum Village", "Sleeping Buddha View"]
    },
    {
        "name": "Roopkund Lake", "state": "Uttarakhand", "avg_travel_cost": 5000.0, "avg_hotel_cost": 0.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 3000.0, "rating": 4.9, "category": "Adventure",
        "best_season": "April to June, September to October", "description": "Mysterious glacial lake at 5029m, known for ancient skeletal remains and challenging high-altitude trek.",
        "attractions": ["Roopkund Lake", "Ali Bugyal meadow", "Bedni Bugyal", "Tungnath side trail"]
    },
    {
        "name": "Coorg Rafting Circuit", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 2000.0, "rating": 4.4, "category": "Adventure",
        "best_season": "June to October", "description": "White-water rafting on River Barapole combined with plantation camping and coffee tasting.",
        "attractions": ["Barapole River Rafting", "Iruppu Falls", "Coffee Estate Walk", "Nagarhole Safari"]
    },

    # ADDITIONAL CITY EXPLORATION
    {
        "name": "Agra", "state": "Uttar Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 350.0, "rating": 4.6, "category": "City Exploration",
        "best_season": "October to March", "description": "City of the Taj Mahal, Agra Fort, and Mughal architectural marvels along the Yamuna.",
        "attractions": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri", "Mehtab Bagh"]
    },
    {
        "name": "Jodhpur", "state": "Rajasthan", "avg_travel_cost": 1900.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 300.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "The Blue City dominated by the colossal Mehrangarh Fort, vibrant bazaars, and spicy Mirchi Bada.",
        "attractions": ["Mehrangarh Fort", "Jaswant Thada", "Clock Tower Market", "Umaid Bhawan Palace"]
    },
    {
        "name": "Bhopal", "state": "Madhya Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 250.0, "rating": 4.1, "category": "City Exploration",
        "best_season": "October to March", "description": "City of Lakes with Mughal mosques, tribal museums, and gateway access to Bhimbetka cave paintings.",
        "attractions": ["Upper Lake", "Bhimbetka Rock Shelters", "Bhojpur Temple", "Tribal Museum"]
    },
    {
        "name": "Varanasi Heritage Walk", "state": "Uttar Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 250.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "Living heritage city where ancient ghats, silk weaving lanes, and daily rituals form an unmatched tableaux.",
        "attractions": ["Dashashwamedh Ghat", "Vishwanath Gali", "Boat Ride at Dawn", "Banaras Hindu University"]
    },
    {
        "name": "Puri Heritage Walk", "state": "Odisha", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 230.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "Spiritual coastal city with grand Jagannath Temple, pattachitra paintings, and famous chhena poda desserts.",
        "attractions": ["Jagannath Temple", "Sudarshan Crafts Museum", "Marine Drive", "Raghurajpur Artisan Village"]
    },
    {
        "name": "Cuttack", "state": "Odisha", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.0, "category": "City Exploration",
        "best_season": "October to March", "description": "Odisha's Silver City famous for filigree jewellery, Barabati Fort, and the grand Durga Puja pandals.",
        "attractions": ["Barabati Fort", "Kadam Rasul Mosque", "Stone Revetment", "Taladanda Canal Walk"]
    },

    # ADDITIONAL HERITAGE & CULTURAL
    {
        "name": "Hampi Heritage Circuit", "state": "Karnataka", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1100.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 350.0, "rating": 4.8, "category": "City Exploration",
        "best_season": "October to March", "description": "Beyond the main ruins — lesser-visited temples, rice-paddy sunrises, and coracle rides on the Tungabhadra.",
        "attractions": ["Tungabhadra Coracle Ride", "Sasivekalu Ganesha", "Anegundi Village", "Lotus Mahal"]
    },
    {
        "name": "Khajuraho", "state": "Madhya Pradesh", "avg_travel_cost": 2500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "UNESCO temples with intricate erotic sculptures, classical dance festivals, and quiet medieval alleys.",
        "attractions": ["Western Temples Group", "Eastern Temples Group", "Khajuraho Light & Sound Show", "Ken Gharial Sanctuary"]
    },
    {
        "name": "Sanchi", "state": "Madhya Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1400.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 200.0, "rating": 4.4, "category": "Religious",
        "best_season": "October to March", "description": "UNESCO Buddhist monument site with the Great Stupa, ancient carved toranas, and peaceful surroundings.",
        "attractions": ["Great Stupa of Sanchi", "Ashoka Pillar", "Museum", "Udayagiri Caves"]
    },
    {
        "name": "Orchha", "state": "Madhya Pradesh", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 250.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "Forgotten Bundela capital on the Betwa River, with towering cenotaphs and temple spires reflected in the water.",
        "attractions": ["Jahangir Mahal", "Ram Raja Temple", "Chaturbhuj Temple", "Orchha Cenotaphs"]
    },
    {
        "name": "Mandu", "state": "Madhya Pradesh", "avg_travel_cost": 2000.0, "avg_hotel_cost": 1500.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 250.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "July to October", "description": "Romantic ruined city perched on a plateau, transformed brilliantly by monsoon greenery.",
        "attractions": ["Jahaz Mahal", "Hindola Mahal", "Rani Roopmati Pavilion", "Baz Bahadur Palace"]
    },

    # ADDITIONAL ROMANTIC
    {
        "name": "Coorg Couple Trail", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 600.0, "rating": 4.6, "category": "Romantic",
        "best_season": "October to April", "description": "Luxury plantation cottages, misty mornings, and waterfall picnics for couples.",
        "attractions": ["Iruppu Falls", "Abbey Falls", "Coffee Plantation Stay", "Raja's Seat Sunset"]
    },
    {
        "name": "Pondicherry Couple Escape", "state": "Tamil Nadu", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 400.0, "rating": 4.4, "category": "Romantic",
        "best_season": "October to March", "description": "Cobblestone French colonial streets, boutique bistros, and seaside promenades perfect for couples.",
        "attractions": ["French Quarter Walk", "Promenade Beach Sunset", "Sri Aurobindo Ashram", "Paradise Beach Ferry"]
    },
    {
        "name": "Andaman Islands Romantic Escape", "state": "Andaman & Nicobar", "avg_travel_cost": 9000.0, "avg_hotel_cost": 5000.0,
        "avg_food_cost": 1200.0, "avg_activity_cost": 2200.0, "rating": 4.8, "category": "Romantic",
        "best_season": "November to April", "description": "Bioluminescent beaches, private island sunset cruises, and couple snorkelling in coral lagoons.",
        "attractions": ["Radhanagar Beach Sunset", "Glass Bottom Boat Ride", "Ross Island", "Sawai Island Picnic"]
    },
    {
        "name": "Binsar", "state": "Uttarakhand", "avg_travel_cost": 2800.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "Romantic",
        "best_season": "March to June, September to November", "description": "Private forested estate viewpoints overlooking 300km of Himalayan peaks, wildlife, and birdsong.",
        "attractions": ["Binsar Wildlife Sanctuary", "Zero Point Panorama", "Kasar Devi Temple", "Sunrise Forest Walk"]
    },

    # ADDITIONAL FAMILY
    {
        "name": "Coorg Family Holiday", "state": "Karnataka", "avg_travel_cost": 2200.0, "avg_hotel_cost": 2400.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 600.0, "rating": 4.5, "category": "Family",
        "best_season": "October to April", "description": "Kids enjoy elephant encounters, jungle trails, and coffee estate scavenger hunts.",
        "attractions": ["Dubare Elephant Camp", "Abbey Falls", "Kodava Cultural Show", "Nagarhole Day Trip"]
    },
    {
        "name": "Gangtok Family Sikkim", "state": "Sikkim", "avg_travel_cost": 4500.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 700.0, "rating": 4.5, "category": "Family",
        "best_season": "March to May, September to December", "description": "Beautiful orchid houses, cable car rides, and colourful Rumtek Monastery for family exploration.",
        "attractions": ["Tsomgo Lake", "Rumtek Monastery", "Gangtok Ropeway", "Flower Exhibition Centre"]
    },
    {
        "name": "Agra Family Heritage", "state": "Uttar Pradesh", "avg_travel_cost": 1500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 400.0, "rating": 4.6, "category": "Family",
        "best_season": "October to March", "description": "Children are enthralled by Taj Mahal, the maze-like Agra Fort, and the unique city of Fatehpur Sikri.",
        "attractions": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri", "Shilpgram Crafts Mela"]
    },
    {
        "name": "Sikkim Nature Family", "state": "Sikkim", "avg_travel_cost": 5000.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 900.0, "rating": 4.7, "category": "Family",
        "best_season": "April to June", "description": "Rhododendron forests, yak rides at Tsomgo lake, and monastery learning experiences for families.",
        "attractions": ["Tsomgo Lake Yak Ride", "Nathula Border", "Pemayangtse Monastery", "Orchid Sanctuary"]
    },

    # ADDITIONAL SOLO
    {
        "name": "Bir Billing Solo", "state": "Himachal Pradesh", "avg_travel_cost": 2200.0, "avg_hotel_cost": 900.0,
        "avg_food_cost": 450.0, "avg_activity_cost": 2500.0, "rating": 4.6, "category": "Solo",
        "best_season": "October to June", "description": "A solo traveler's paragliding dream, with budget cafes, dhaba food, and a thriving backpacker scene.",
        "attractions": ["Billing Takeoff Meadow", "Sherabling Monastery", "Bir Village Market", "Trial Paragliding"]
    },
    {
        "name": "Spiti Summer Solo", "state": "Himachal Pradesh", "avg_travel_cost": 5000.0, "avg_hotel_cost": 1200.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 1200.0, "rating": 4.8, "category": "Solo",
        "best_season": "June to September", "description": "Extreme offbeat cold desert solo expedition with homestays in remote villages like Langza and Komic.",
        "attractions": ["Ki Monastery", "Hikkim Post Office", "Langza Buddha Statue", "Komik Highest Village"]
    },
    {
        "name": "Darjeeling Tea Trail Solo", "state": "West Bengal", "avg_travel_cost": 3000.0, "avg_hotel_cost": 1100.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 400.0, "rating": 4.5, "category": "Solo",
        "best_season": "October to May", "description": "Tea garden walks, monastery hopping, and sunrise treks for the contemplative solo explorer.",
        "attractions": ["Happy Valley Tea Estate", "Batasia Loop Walk", "Peace Pagoda", "Singalila Ridge Day Walk"]
    },
    {
        "name": "Hampi Ruins Solo", "state": "Karnataka", "avg_travel_cost": 1800.0, "avg_hotel_cost": 800.0,
        "avg_food_cost": 400.0, "avg_activity_cost": 350.0, "rating": 4.8, "category": "Solo",
        "best_season": "October to March", "description": "Ruins cycling, sunrise boulder climbs, and riverside meditation for solo history lovers.",
        "attractions": ["Matanga Hill Sunrise", "Vitthala Temple", "Hippy Island", "Coracle Ride"]
    },

    # WILDLIFE / SAFARI
    {
        "name": "Ranthambore", "state": "Rajasthan", "avg_travel_cost": 2500.0, "avg_hotel_cost": 3500.0,
        "avg_food_cost": 800.0, "avg_activity_cost": 2000.0, "rating": 4.6, "category": "Adventure",
        "best_season": "October to June", "description": "India's most famous tiger reserve with ancient Ranthambore Fort inside the safari zone.",
        "attractions": ["Ranthambore Tiger Safari", "Ranthambore Fort", "Padam Lake", "Malik Talao"]
    },
    {
        "name": "Sundarbans", "state": "West Bengal", "avg_travel_cost": 3500.0, "avg_hotel_cost": 1800.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 1500.0, "rating": 4.5, "category": "Adventure",
        "best_season": "September to February", "description": "UNESCO mangrove delta, unique boat safaris for Royal Bengal Tigers and estuarine crocodiles.",
        "attractions": ["Sajnekhali Tiger Reserve", "Sudhanyakhali Watch Tower", "Dobanki Camp Walk", "Netidhopani Ruins"]
    },
    {
        "name": "Kaziranga National Park", "state": "Assam", "avg_travel_cost": 3800.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 1800.0, "rating": 4.8, "category": "Adventure",
        "best_season": "November to April", "description": "UNESCO park hosting two-thirds of world's one-horned rhinoceros population; famous elephant safaris.",
        "attractions": ["Elephant Safari", "Jeep Safari", "Orchid Park", "Kohora Zone"]
    },
    {
        "name": "Periyar Wildlife Circuit", "state": "Kerala", "avg_travel_cost": 2800.0, "avg_hotel_cost": 2200.0,
        "avg_food_cost": 650.0, "avg_activity_cost": 1200.0, "rating": 4.5, "category": "Adventure",
        "best_season": "September to April", "description": "Jungle patrols, bamboo rafting, and boat rides spotting wild elephants at Periyar Lake.",
        "attractions": ["Periyar Boat Ride", "Bamboo Rafting", "Nature Walk", "Spice Plantation Visit"]
    },
    {
        "name": "Bandhavgarh", "state": "Madhya Pradesh", "avg_travel_cost": 3000.0, "avg_hotel_cost": 3000.0,
        "avg_food_cost": 750.0, "avg_activity_cost": 2200.0, "rating": 4.6, "category": "Adventure",
        "best_season": "October to June", "description": "Highest density tiger reserve in India with ancient caves and a ruined hilltop fort.",
        "attractions": ["Tala Zone Safari", "Bandhavgarh Fort", "Bamera Zone", "Vulture Point"]
    },
    {
        "name": "Pench National Park", "state": "Madhya Pradesh", "avg_travel_cost": 2800.0, "avg_hotel_cost": 2800.0,
        "avg_food_cost": 700.0, "avg_activity_cost": 2000.0, "rating": 4.4, "category": "Adventure",
        "best_season": "October to June", "description": "Inspiration for Rudyard Kipling's Jungle Book, with tigers, leopards, and painted storks.",
        "attractions": ["Core Zone Jeep Safari", "Jamtara Wilderness Walk", "Pench River Walk", "Bird Watching Tower"]
    },

    # NORTHEASTERN CULTURAL
    {
        "name": "Shillong", "state": "Meghalaya", "avg_travel_cost": 4500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 400.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "March to June, September to November", "description": "Scotland of the East with rolling pine hills, colonial churches, and a thriving live music scene.",
        "attractions": ["Elephant Falls", "Ward's Lake", "Shillong Peak", "Police Bazaar Market"]
    },
    {
        "name": "Dimapur", "state": "Nagaland", "avg_travel_cost": 5000.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 500.0, "rating": 4.1, "category": "City Exploration",
        "best_season": "October to March", "description": "Entry point to Nagaland, famed for the unique Kachari kingdom ruins and Hornbill Festival access.",
        "attractions": ["Kachari Ruins", "Nagaland Zoological Park", "Dzukou Valley Base", "Hornbill Festival (December)"]
    },
    {
        "name": "Imphal", "state": "Manipur", "avg_travel_cost": 5500.0, "avg_hotel_cost": 2000.0,
        "avg_food_cost": 550.0, "avg_activity_cost": 500.0, "rating": 4.3, "category": "City Exploration",
        "best_season": "October to March", "description": "City of gardens and legacy WWII battlefields, gateway to Loktak floating lake and Keibul Lamjao Park.",
        "attractions": ["Loktak Lake Floating Islands", "Ima Keithel Women's Market", "Kangla Fort", "Keibul Lamjao National Park"]
    },

    # HERITAGE COASTAL
    {
        "name": "Mahabalipuram Heritage", "state": "Tamil Nadu", "avg_travel_cost": 1500.0, "avg_hotel_cost": 1900.0,
        "avg_food_cost": 600.0, "avg_activity_cost": 350.0, "rating": 4.4, "category": "City Exploration",
        "best_season": "October to March", "description": "UNESCO rock-cut temples by the sea; surfing schools, stone carving workshops, and seafood shacks.",
        "attractions": ["Shore Temple", "Descent of the Ganges", "Five Rathas", "Tiger Cave"]
    },
    {
        "name": "Tranquebar", "state": "Tamil Nadu", "avg_travel_cost": 1800.0, "avg_hotel_cost": 1600.0,
        "avg_food_cost": 500.0, "avg_activity_cost": 200.0, "rating": 4.1, "category": "City Exploration",
        "best_season": "October to March", "description": "Tiny, well-preserved Danish colonial settlement with a fort, sea walls, and quiet beach walks.",
        "attractions": ["Dansborg Fort", "New Jerusalem Church", "Tranquebar Beach", "Masilamani Nathar Temple"]
    },
    {
        "name": "Fort Kochi Heritage Walk", "state": "Kerala", "avg_travel_cost": 3200.0, "avg_hotel_cost": 2500.0,
        "avg_food_cost": 750.0, "avg_activity_cost": 350.0, "rating": 4.5, "category": "City Exploration",
        "best_season": "October to March", "description": "Heritage bungalows, antique streets, artist cafes, and famous Chinese fishing nets at dusk.",
        "attractions": ["Chinese Fishing Nets", "Indo-Portuguese Museum", "Mattancherry Palace", "Jew Town Antiques"]
    }
]

def get_expanded_fields(name: str, category: str, avg_hotel_cost: float) -> dict:
    # Budget tier
    if avg_hotel_cost < 1600:
        budget_tier = "Budget"
        comfort_level = 30
    elif avg_hotel_cost <= 2800:
        budget_tier = "Mid-range"
        comfort_level = 60
    else:
        budget_tier = "Premium"
        comfort_level = 85
        
    # Duration
    if name in [
        "Havelock Island", "Neil Island", "Lakshadweep", "Leh Ladakh", "Spiti Valley", "Zanskar Valley",
        "Tawang", "Gulmarg", "Gulmarg Valley", "Srinagar", "Alleppey Houseboat", "Chadar Trek"
    ]:
        recommended_duration = 6
    elif name in [
        "North Goa", "South Goa", "Munnar", "Coorg", "Ooty", "Darjeeling", "Manali", "Rishikesh",
        "Auli", "Wayanad", "Hampi", "Meghalaya Caves", "Kerala Family Backwaters"
    ]:
        recommended_duration = 4
    else:
        recommended_duration = 3
        
    # Scores out of 100
    scores = {
        "adventure_score": 30.0,
        "nature_score": 30.0,
        "family_score": 50.0,
        "romantic_score": 30.0,
        "religious_score": 10.0,
        "beach_score": 10.0,
        "city_score": 10.0,
        "solo_score": 40.0
    }
    
    if category == "Beach":
        scores.update({"beach_score": 90.0, "romantic_score": 75.0, "family_score": 70.0, "adventure_score": 50.0})
    elif category == "Nature":
        scores.update({"nature_score": 95.0, "romantic_score": 70.0, "family_score": 80.0, "adventure_score": 40.0})
    elif category == "Adventure":
        scores.update({"adventure_score": 95.0, "nature_score": 80.0, "solo_score": 85.0, "family_score": 40.0})
    elif category == "Religious":
        scores.update({"religious_score": 95.0, "family_score": 85.0, "nature_score": 40.0})
    elif category == "City Exploration":
        scores.update({"city_score": 90.0, "family_score": 75.0, "romantic_score": 50.0, "nature_score": 20.0})
    elif category == "Romantic":
        scores.update({"romantic_score": 95.0, "nature_score": 80.0, "family_score": 50.0, "beach_score": 40.0})
    elif category == "Family":
        scores.update({"family_score": 95.0, "nature_score": 70.0, "beach_score": 45.0, "adventure_score": 35.0, "solo_score": 20.0})
    elif category == "Solo":
        scores.update({"solo_score": 90.0, "adventure_score": 75.0, "nature_score": 70.0, "family_score": 25.0})

    # Individual variations
    if "Goa" in name:
        scores["beach_score"] = 95.0
        scores["romantic_score"] = 80.0
    if "Rishikesh" in name:
        scores["religious_score"] = 85.0
        scores["adventure_score"] = 90.0
    if "Leh Ladakh" in name or "Spiti" in name:
        scores["adventure_score"] = 98.0
        scores["nature_score"] = 95.0
        scores["solo_score"] = 95.0
    if "Varanasi" in name or "Kedarnath" in name or "Badrinath" in name:
        scores["religious_score"] = 99.0
    if "Hampi" in name:
        scores["solo_score"] = 95.0
        scores["city_score"] = 70.0
        
    return {
        "budget_tier": budget_tier,
        "recommended_duration": recommended_duration,
        "comfort_level": comfort_level,
        **scores
    }

def seed_destinations(db: Session):
    existing_names = {name for (name,) in db.query(Destination.name).all()}
    added = 0

    # Seed original destinations
    for dest_data in DESTINATIONS_DATA:
        if dest_data["name"] in existing_names:
            continue
        expanded = get_expanded_fields(dest_data["name"], dest_data["category"], dest_data["avg_hotel_cost"])
        db_destination = Destination(**dest_data, **expanded)
        db.add(db_destination)
        added += 1

    # Seed international and enhanced destinations
    for dest_data in INTERNATIONAL_DESTINATIONS:
        if dest_data["name"] in existing_names:
            continue
        # Already have expanded fields in enhanced data
        db_destination = Destination(**dest_data)
        db.add(db_destination)
        added += 1

    if added:
        db.commit()
        total = db.query(Destination).count()
        print(f"Seeded {added} new destinations ({total} total in database).")
    else:
        total = db.query(Destination).count()
        print(f"Database already up to date with {total} destinations.")
