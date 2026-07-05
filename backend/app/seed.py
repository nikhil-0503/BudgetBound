from sqlalchemy.orm import Session
from app.models import Destination

DESTINATIONS_DATA = [
    # BEACH (10)
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
    
    # NATURE (10)
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

    # ADVENTURE (10)
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

    # RELIGIOUS (10)
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

    # CITY EXPLORATION (10)
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

    # ROMANTIC (10)
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
    if name in ["Havelock Island", "Leh Ladakh", "Spiti Valley", "Tawang", "Gulmarg", "Gulmarg Valley", "Srinagar", "Alleppey Houseboat"]:
        recommended_duration = 6
    elif name in ["North Goa", "South Goa", "Munnar", "Coorg", "Ooty", "Darjeeling", "Manali", "Rishikesh", "Auli", "Wayanad"]:
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
    if "Varanasi" in name or "Kedarnath" in name:
        scores["religious_score"] = 99.0
        
    return {
        "budget_tier": budget_tier,
        "recommended_duration": recommended_duration,
        "comfort_level": comfort_level,
        **scores
    }

def seed_destinations(db: Session):
    count = db.query(Destination).count()
    if count == 0:
        print(f"Seeding {len(DESTINATIONS_DATA)} destinations into the database...")
        for dest_data in DESTINATIONS_DATA:
            expanded = get_expanded_fields(dest_data["name"], dest_data["category"], dest_data["avg_hotel_cost"])
            db_destination = Destination(**dest_data, **expanded)
            db.add(db_destination)
        db.commit()
        print("Seeding completed successfully!")
    else:
        print(f"Database already contains {count} destinations. Seeding skipped.")
