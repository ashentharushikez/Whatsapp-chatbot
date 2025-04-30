from asyncio import run
from flask import Flask, request, jsonify
import os
import traceback
import re
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required environment variables
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.error("Missing GOOGLE_API_KEY environment variable. Set this in your .env file.")
    # We'll continue and handle this in the AI response function

# Initialize Flask app
app = Flask(__name__)

# Store user states
chat_states = {}

# Define messages that would normally be in responses.py
# You should move these to a separate file later
MESSAGES = {
    "english": {
        "welcome": "Welcome to Sun Mobile Horana!\n\nPlease select your preferred language:\n1. English\n2. සිංහල (Sinhala)\n3. Singlish\n\nReply with the number of your choice.",
        "menu": "How can I help you today? You can ask about our:\n- Mobile phones and brands\n- Accessories\n- Repair services\n- Location and contact details\n\nOr type your question directly!",
        "error": "I apologize for the inconvenience. There seems to be a technical issue. Please try again or call us directly at 0767410963."
    },
    "sinhala": {
        "welcome": "සුන් මොබයිල් හොරණ වෙත සාදරයෙන් පිළිගනිමු!\n\nකරුණාකර ඔබගේ භාෂාව තෝරන්න:\n1. English\n2. සිංහල (Sinhala)\n3. Singlish\n\nඔබගේ තේරීම සමඟ පිළිතුරු දෙන්න.",
        "menu": "මට අද ඔබට කෙසේ උදව් කළ හැකිද? ඔබට අසන්න පුළුවන්:\n- ජංගම දුරකථන සහ වෙළඳ නාම\n- උපාංග\n- අලුත්වැඩියා සේවා\n- ස්ථානය සහ සම්බන්ධතා විස්තර\n\nහෝ ඔබේ ප්‍රශ්නය කෙලින්ම ටයිප් කරන්න!",
        "error": "අපහසුතාවය ගැන මම සමාව අයැද සිටිමි. තාක්ෂණික ගැටලුවක් ඇති බව පෙනේ. කරුණාකර නැවත උත්සාහ කරන්න හෝ 0767410963 අංකයෙන් අප අමතන්න."
    },
    "singlish": {
        "welcome": "Sun Mobile Horana ekata welcome!\n\nOyage language eka thoranna:\n1. English\n2. සිංහල (Sinhala)\n3. Singlish\n\nOyage choice eka reply karanna.",
        "menu": "Mata ada oyata kohomada help karanne? Oyata ahanna puluwan:\n- Mobile phones saha brands\n- Accessories\n- Repair services\n- Location saha contact details\n\nNathnam oyage question eka directly type karanna!",
        "error": "Mama sorry, technical issue ekak thiyenawa wage. Please try again or call karanna 0767410963."
    }
}

# Define FAQ responses
FAQ_RESPONSES = {
    "english": {
        "warranty": "All our repair services come with a warranty. For phones, we offer a 6-month warranty on hardware repairs and 3 months on software services. For accessories, warranty depends on the manufacturer, typically 3-12 months.",
        "payment": "We accept cash, card payments (Visa/Mastercard), bank transfers, and mobile payment apps like FriMi and eZ Cash.",
        "delivery": "Yes, we offer island-wide delivery with a small fee based on your location. Delivery typically takes 1-3 business days.",
        "hours": "We're open from 9:00 AM to 8:00 PM, seven days a week including holidays.",
        "returns": "We have a 7-day return policy for unopened products in their original packaging. For defective items, please return within 14 days for a replacement."
    },
    "sinhala": {
        "warranty": "අපගේ සියලුම අලුත්වැඩියා සේවා සඳහා වගකීමක් ඇත. දුරකථන සඳහා, අපි දෘඩාංග අලුත්වැඩියා සඳහා මාස 6 ක වගකීමක් සහ මෘදුකාංග සේවා සඳහා මාස 3 ක් ලබා දෙන්නෙමු. උපාංග සඳහා, වගකීම නිෂ්පාදකයා මත රඳා පවතී, සාමාන්‍යයෙන් මාස 3-12.",
        "payment": "අපි මුදල්, කාඩ්පත් ගෙවීම් (Visa/Mastercard), බැංකු මාරු, සහ FriMi සහ eZ Cash වැනි ජංගම ගෙවීම් යෙදුම් භාර ගන්නෙමු.",
        "delivery": "ඔව්, අපි ඔබේ ස්ථානය මත පදනම්ව සුළු ගාස්තුවක් සමඟ දිවයින පුරා බෙදා හැරීම් සපයන්නෙමු. බෙදාහැරීම සාමාන්‍යයෙන් ව්‍යාපාරික දින 1-3 ක් ගත වේ.",
        "hours": "අපි නිවාඩු දින ඇතුළුව සතියේ දින හතම උදේ 9:00 සිට රාත්‍රී 8:00 දක්වා විවෘතව ඇත.",
        "returns": "අපට මුල් ඇසුරුම් වල නොවිවෘත නිෂ්පාදන සඳහා දින 7 ක ආපසු භාර දීමේ ප්‍රතිපත්තියක් ඇත. දෝෂ සහිත අයිතම සඳහා, ප්‍රතිස්ථාපනයක් සඳහා කරුණාකර දින 14 ක් ඇතුළත ආපසු දෙන්න."
    },
    "singlish": {
        "warranty": "Ape repair services okkomata warranty thiyenawa. Phones walata, hardware repairs walata maasa 6 warranty ekak saha software services walata maasa 3 warranty ekak denawa. Accessories walata, warranty eka manufacturer eka anuwa wenas wenawa, typically maasa 3-12.",
        "payment": "Api cash, card payments (Visa/Mastercard), bank transfers, saha FriMi saha eZ Cash wage mobile payment apps accept karanawa.",
        "delivery": "Ow, api island-wide delivery small fee ekak ekka provide karanawa based on oyage location eka. Delivery typically business days 1-3 k gatha wenawa.",
        "hours": "Api uday 9:00 idala rathri 8:00 wenakam open, satiye dhavas 7ma holidays day include wela.",
        "returns": "Apita unopened products original packaging eke day 7k return karanna puluwan. Defective items walata, replacement ekak enawanm day 14k athule return karanna."
    }
}

# Mock product images dictionary that would be in responses.py
PRODUCT_IMAGES = {
    "phones": {
        "samsung": {
            "Galaxy S23": "static/images/samsung_s23.jpeg",
            "Galaxy S24": "static/images/samsung_s24.jpeg",
            "Galaxy A54": "static/images/samsung_a54.jpeg"
        },
        "apple": {
            "iPhone 15": "static/images/iphone_15.jpeg",
            "iPhone 15 Pro": "static/images/iphone_15_pro.jpeg",
            "iPhone 14": "static/images/iphone_14.jpeg"
        },
        "xiaomi": {
            "Redmi Note 13 Pro": "static/images/redmi_note13_pro.jpeg",
            "Poco F5": "static/images/poco_f5.jpeg"
        }
    },
    "accessories": {
        "chargers": {
            "Fast Charger 65W": "static/images/fast_charger_65w.jpeg",
            "Wireless Charger": "static/images/wireless_charger.jpeg"
        },
        "cases": {
            "Silicon Case": "static/images/silicon_case.jpeg",
            "Leather Case": "static/images/leather_case.jpeg"
        }
    }
}

class ChatState:
    def __init__(self):
        self.current_stage = "welcome"  # Initial stage
        self.language = "sinhala"  # Default language is Sinhala
        self.customer_name = ""
        self.selected_category = ""
        self.selected_brand = ""
        self.selected_service = ""
        self.conversation_history = []  # To store conversation history
        self.is_first_message = True
        self.inquired_products = []  # Track what products user has asked about
        self.last_activity = time.time()  # Track when this state was last active

    def reset(self):
        saved_language = self.language
        self.__init__()
        self.language = saved_language  # Keep the language preference on reset

    def add_to_history(self, message, response):
        """Add message and response to conversation history"""
        # If response is a dict with 'text', extract just the text part
        response_text = response["text"] if isinstance(response, dict) and "text" in response else response
        
        self.conversation_history.append({"message": message, "response": response_text})
        # Keep only last 10 messages for context
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
        
        # Update last activity timestamp
        self.last_activity = time.time()

# Setup Google AI if API key is available
try:
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Google AI model initialized successfully")
    else:
        model = None
        logger.warning("No API key found, AI responses will be unavailable")
except Exception as e:
    logger.error(f"Failed to initialize Google AI model: {e}")
    model = None

# Enhanced shop information with more specific product details
SHOP_INFO = {
    "english": {
        "name": "Sun Mobile Horana",
        "products": ["mobile phones", "accessories", "repair services", "exchange programs"],
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "popular_models": {
            "Samsung": ["Galaxy S23", "Galaxy S24", "Galaxy A54", "Galaxy A34", "Galaxy Z Fold 5"],
            "Apple": ["iPhone 15", "iPhone 15 Pro", "iPhone 14", "iPhone 14 Pro", "iPhone 13"],
            "Xiaomi": ["Redmi Note 13 Pro", "Redmi 13C", "Poco F5", "Xiaomi 13T"],
            "Oppo": ["Reno 10", "A78", "A18", "Find X6"],
            "Vivo": ["V27", "V29", "Y27", "Y17s"],
            "Huawei": ["Nova 11", "Nova Y90", "P60 Pro"]
        },
        "price_ranges": {
            "Samsung": "Rs. 55,000 - Rs. 450,000",
            "Apple": "Rs. 175,000 - Rs. 585,000",
            "Xiaomi": "Rs. 35,000 - Rs. 180,000",
            "Oppo": "Rs. 40,000 - Rs. 150,000",
            "Vivo": "Rs. 35,000 - Rs. 140,000",
            "Huawei": "Rs. 45,000 - Rs. 200,000"
        },
        "accessories": ["chargers", "headphones", "data cables", "back covers", "tempered glass"],
        "accessories_details": {
            "chargers": ["Fast chargers (18W-65W)", "Wireless chargers", "Car chargers", "Power banks"],
            "headphones": ["Wired earphones", "Bluetooth earbuds", "Over-ear headphones", "Gaming headsets"],
            "data_cables": ["Type-C", "Micro USB", "Lightning cables", "3-in-1 cables"],
            "back_covers": ["Silicon cases", "Hard cases", "Flip covers", "Transparent cases", "Leather cases"],
            "tempered_glass": ["MTB tempered glass", "SUPER D glass", "Privacy glass", "UV glass protectors"]
        },
        "services": ["hardware repairs", "software repairs", "iCloud unlock", "FRP lock removal", 
                    "Mi account unlock", "network unlock", "screen replacement"],
        "repair_costs": {
            "screen_replacement": {
                "Samsung": "Rs. 8,000 - Rs. 45,000",
                "Apple": "Rs. 18,000 - Rs. 75,000",
                "Xiaomi": "Rs. 5,000 - Rs. 20,000",
                "Others": "Rs. 4,500 - Rs. 30,000"
            },
            "battery_replacement": {
                "Samsung": "Rs. 3,500 - Rs. 12,000",
                "Apple": "Rs. 8,000 - Rs. 25,000",
                "Others": "Rs. 2,500 - Rs. 8,000"
            },
            "software_services": {
                "OS update": "Rs. 1,500",
                "Data recovery": "Rs. 2,500 - Rs. 5,000",
                "FRP unlock": "Rs. 2,500 - Rs. 4,000",
                "Factory reset": "Rs. 1,000"
            }
        },
        "address": "No.30 Panadura Road, Horana (In front of the Hall)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "hours": "9:00 AM to 8:00 PM, seven days a week",
        "intro": "I'm the virtual assistant for Sun Mobile Horana. I can help you with information about our products, services, and any other queries you might have.",
        "payment_methods": ["Cash", "Card payments", "Bank transfers", "Online payment apps"],
        "delivery": "Island-wide delivery available, delivery time 1-3 days depending on location"
    },
    "sinhala": {
        "name": "සුන් මොබයිල් හොරණ",
        "products": ["ජංගම දුරකථන", "උපාංග", "අලුත්වැඩියා සේවා", "හුවමාරු පිරිනැමුම්"],
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "popular_models": {
            "Samsung": ["Galaxy S23", "Galaxy S24", "Galaxy A54", "Galaxy A34", "Galaxy Z Fold 5"],
            "Apple": ["iPhone 15", "iPhone 15 Pro", "iPhone 14", "iPhone 14 Pro", "iPhone 13"],
            "Xiaomi": ["Redmi Note 13 Pro", "Redmi 13C", "Poco F5", "Xiaomi 13T"],
            "Oppo": ["Reno 10", "A78", "A18", "Find X6"],
            "Vivo": ["V27", "V29", "Y27", "Y17s"],
            "Huawei": ["Nova 11", "Nova Y90", "P60 Pro"]
        },
        "price_ranges": {
            "Samsung": "රු. 55,000 - රු. 450,000",
            "Apple": "රු. 175,000 - රු. 585,000",
            "Xiaomi": "රු. 35,000 - රු. 180,000",
            "Oppo": "රු. 40,000 - රු. 150,000",
            "Vivo": "රු. 35,000 - රු. 140,000",
            "Huawei": "රු. 45,000 - රු. 200,000"
        },
        "accessories": ["චාජර්", "හෙඩ්ෆෝන්", "දත්ත කේබල්", "පිටුපස ආවරණ", "ටෙම්පර්ඩ් ග්ලාස්"],
        "accessories_details": {
            "chargers": ["වේගවත් චාජර් (18W-65W)", "රැහැන් රහිත චාජර්", "කාර් චාජර්", "පවර් බෑන්ක්"],
            "headphones": ["රැහැන් සහිත ඉයර්ෆෝන්", "බ්ලූටූත් ඉයර්බඩ්ස්", "කන් වටා හෙඩ්ෆෝන්", "ගේමිං හෙඩ්සෙට්"],
            "data_cables": ["Type-C", "Micro USB", "Lightning කේබල්", "3-in-1 කේබල්"],
            "back_covers": ["සිලිකන් කවර", "හාඩ් කවර", "ෆ්ලිප් කවර", "විනිවිද පෙනෙන කවර", "සම් කවර"],
            "tempered_glass": ["MTB ටෙම්පර්ඩ් ග්ලාස්", "SUPER D ග්ලාස්", "ප්‍රයිවසි ග්ලාස්", "UV ග්ලාස් ආරක්ෂක"]
        },
        "services": ["හාඩ්වෙයාර් අලුත්වැඩියා", "සොෆ්ට්වෙයාර් අලුත්වැඩියා", "iCloud අගුළු ඉවත් කිරීම", 
                    "FRP අගුළු ඉවත් කිරීම", "Mi ගිණුම් අගුළු ඉවත් කිරීම", "ජාල අගුළු විවෘත කිරීම", "තිර ප්‍රතිස්ථාපනය"],
        "repair_costs": {
            "screen_replacement": {
                "Samsung": "රු. 8,000 - රු. 45,000",
                "Apple": "රු. 18,000 - රු. 75,000",
                "Xiaomi": "රු. 5,000 - රු. 20,000",
                "Others": "රු. 4,500 - රු. 30,000"
            },
            "battery_replacement": {
                "Samsung": "රු. 3,500 - රු. 12,000",
                "Apple": "රු. 8,000 - රු. 25,000",
                "Others": "රු. 2,500 - රු. 8,000"
            },
            "software_services": {
                "OS update": "රු. 1,500",
                "Data recovery": "රු. 2,500 - රු. 5,000",
                "FRP unlock": "රු. 2,500 - රු. 4,000",
                "Factory reset": "රු. 1,000"
            }
        },
        "address": "අංක 30, පානදුර පාර, හොරණ (හෝල් එක ඉස්සරහ)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "hours": "උදේ 9:00 සිට රාත්‍රී 8:00 දක්වා, සතියේ දින හතම",
        "intro": "මම සුන් මොබයිල් හොරණ හි virtual සහායකයා වෙමි. මට ඔබට අපගේ නිෂ්පාදන, සේවා සහ ඔබට තිබිය හැකි වෙනත් ඕනෑම ප්‍රශ්නයක් පිළිබඳ තොරතුරු සමඟ උදව් කළ හැකිය.",
        "payment_methods": ["මුදල්", "කාඩ්පත් ගෙවීම්", "බැංකු මාරු කිරීම්", "මාර්ගගත ගෙවීම් යෙදුම්"],
        "delivery": "දිවයින පුරා බෙදාහැරීම ලබා ගත හැකිය, බෙදාහැරීමේ කාලය ස්ථානය අනුව දින 1-3 දක්වා වෙනස් වේ"
    },
    "singlish": {
        "name": "Sun Mobile Horana",
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "services": ["hardware repairs", "software repairs", "iCloud unlock", "FRP unlock", "screen replacement"],
        "address": "No.30 Panadura Road, Horana (Hall eka issaraha)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "intro": "Mata Sun Mobile Horana virtual assistant. Oyage products, services saha questions walata help karanna puluwan."
    }
}

# Add stock information to SHOP_INFO
SHOP_INFO["english"]["stock"] = {
    "Samsung Galaxy S23": 10,
    "iPhone 15": 5,
    "Redmi Note 13 Pro": 15,
    "Oppo Reno 10": 8,
    "Vivo V27": 12,
    "Huawei Nova 11": 7,
    "Fast chargers": 20,
    "Bluetooth earbuds": 25,
    "MTB tempered glass": 30
}

SHOP_INFO["sinhala"]["stock"] = {
    "Samsung Galaxy S23": 10,
    "iPhone 15": 5,
    "Redmi Note 13 Pro": 15,
    "Oppo Reno 10": 8,
    "Vivo V27": 12,
    "Huawei Nova 11": 7,
    "වේගවත් චාජර්": 20,
    "බ්ලූටූත් ඉයර්බඩ්ස්": 25,
    "MTB ටෙම්පර්ඩ් ග්ලාස්": 30
}

# Intent recognition patterns for common questions
INTENTS = {
    "english": {
        "product_inquiry": [
            r"do you (have|sell|offer) (.*?)(phone|iphone|samsung|xiaomi|oppo|vivo|huawei|apple|redmi)?",
            r"(looking for|need|want) (a|an) (.*?)(phone|iphone|samsung|xiaomi|oppo|vivo|huawei|apple|redmi)",
            r"(is|are) (.*?)(phone|iphone|samsung|xiaomi|oppo|vivo|huawei|apple|redmi) available",
            r"price of (.*?)(phone|iphone|samsung|xiaomi|oppo|vivo|huawei|apple|redmi)"
        ],
        "accessory_inquiry": [
            r"do you (have|sell|offer) (.*?)(charger|cable|cover|case|glass|headphone|earphone|earbud)",
            r"(looking for|need|want) (a|an) (.*?)(charger|cable|cover|case|glass|headphone|earphone|earbud)",
            r"(is|are) (.*?)(charger|cable|cover|case|glass|headphone|earphone|earbud) available"
        ],
        "repair_inquiry": [
            r"(can|could) you (fix|repair|replace) (my|the) (.*?)(screen|battery|phone|software|hardware)",
            r"(how much|what) (would it|does it|will it) cost to (fix|repair|replace) (.*?)(screen|battery)",
            r"(is|are) (.*?) (repair|screen replacement|battery replacement) (possible|available)"
        ],
        "location_inquiry": [
            r"(where|what) is your (location|address|shop)",
            r"(how|where) (can|do) I (find|reach|get to) (your shop|your store|you)",
            r"(where are you|where is the shop) (located|situated)"
        ],
        "contact_inquiry": [
            r"(what is|what's) your (contact|phone|number)",
            r"(how|can) (can|do) I (contact|call|reach) you",
            r"(can|could) you (give|share) (me|your) (number|contact|details)"
        ],
        "hours_inquiry": [
            r"(when|what time) (are you|is the shop|is the store) (open|closed)",
            r"(what are|what's) your (hours|business hours|working hours|opening hours)"
        ],
        "delivery_inquiry": [
            r"do you (offer|have|provide) (delivery|shipping)",
            r"(can|will) you (deliver|ship) to (.*?)",
            r"(how long|how much time) (will|does) (delivery|shipping) take"
        ],
        "warranty_inquiry": [
            r"(what|how long) is the (warranty|guarantee) (period|duration)",
            r"(is|are) (.*?) (covered|included) (in|under) (warranty|guarantee)",
            r"do you (offer|provide|give) (warranty|guarantee) (for|on) (.*?)"
        ],
        "stock_inquiry": [
            r"(do you have|is there|are there) (.*?) in stock",
            r"(how many|availability of) (.*?)",
            r"(is|are) (.*?) available"
        ]
    },
    "sinhala": {
        "product_inquiry": [
            r"(.*?)(දුරකථන|ෆෝන්|අයිෆෝන්|සැම්සං|ෂාඕමි|ඔප්පෝ|විවෝ|හුවාවේ|ඇපල්|රෙඩ්මි)(.*?) තියෙනවද",
            r"(.*?)(දුරකථන|ෆෝන්|අයිෆෝන්|සැම්සං|ෂාඕමි|ඔප්පෝ|විවෝ|හුවාවේ|ඇපල්|රෙඩ්මි)(.*?) විකුණනවද",
            r"(.*?)(දුරකථන|ෆෝන්|අයිෆෝන්|සැම්සං|ෂාඕමි|ඔප්පෝ|විවෝ|හුවාවේ|ඇපල්|රෙඩ්මි)(.*?) මිල කීයද"
        ],
        "accessory_inquiry": [
            r"(.*?)(චාජර්|කේබල්|කවර|කේස්|ග්ලාස්|හෙඩ්ෆෝන්|ඉයර්ෆෝන්|ඉයර්බඩ්)(.*?) තියෙනවද",
            r"(.*?)(චාජර්|කේබල්|කවර|කේස්|ග්ලාස්|හෙඩ්ෆෝන්|ඉයර්ෆෝන්|ඉයර්බඩ්)(.*?) විකුණනවද",
            r"(.*?)(චාජර්|කේබල්|කවර|කේස්|ග්ලාස්|හෙඩ්ෆෝන්|ඉයර්ෆෝන්|ඉයර්බඩ්)(.*?) මිල කීයද"
        ],
        "repair_inquiry": [
            r"(.*?)(තිරය|බැටරිය|දුරකථනය|සොෆ්ට්වෙයාර්|හාඩ්වෙයාර්)(.*?) හදන්න පුළුවන්ද",
            r"(.*?)(තිරය|බැටරිය|දුරකථනය|සොෆ්ට්වෙයාර්|හාඩ්වෙයාර්)(.*?) හදන්න කීයක් වෙයිද",
            r"(.*?)(අලුත්වැඩියා|තිර ප්‍රතිස්ථාපනය|බැටරි ප්‍රතිස්ථාපනය)(.*?) කරනවද"
        ],
        "location_inquiry": [
            r"(.*?)(ලිපිනය|ස්ථානය|කොහේද|කොහෙද)(.*?) තියෙන්නේ",
            r"(.*?)(යන්නේ|ලඟා වෙන්නේ|සොයා ගන්නේ) කොහොමද"
        ],
        "contact_inquiry": [
            r"(.*?)(දුරකථන අංකය|අංකය|ඇමතීම)(.*?) මොකක්ද",
            r"(.*?)(සම්බන්ධ වෙන්නේ|අමතන්නේ) කොහොමද"
        ],
        "hours_inquiry": [
            r"(.*?)(විවෘත|වසා) කරන වේලාව(.*?) මොකක්ද",
            r"(.*?)(වැඩ කරන|විවෘත) වේලාවන්(.*?) මොනවාද"
        ],
        "stock_inquiry": [
            r"(.*?)(තිබේද|ඇතිද|ඇවිත්ද)",
            r"(.*?)(කීයක් තියෙන්නේ|ඇවිත් තියෙන්නේ)"
        ]
    }
}

def detect_intent(message, language):
    """Detect the user's intent from their message"""
    intents = INTENTS.get(language, INTENTS["english"])
    
    for intent, patterns in intents.items():
        for pattern in patterns:
            if re.search(pattern, message.lower()):
                return intent
    
    return "general"

def extract_product_details(message, language):
    """Extract product or service details from the message"""
    details = {}
    
    # Extract brand
    brands = SHOP_INFO[language]["brands"]
    for brand in brands:
        if brand.lower() in message.lower():
            details["brand"] = brand
            break
    
    # Extract product model (simplified approach)
    # For iPhone models
    iphone_match = re.search(r"iphone\s*(\d+)(?:\s*(pro|plus|max))?", message.lower())
    if iphone_match:
        model_num = iphone_match.group(1)
        variant = iphone_match.group(2) or ""
        details["model"] = f"iPhone {model_num}{' ' + variant.capitalize() if variant else ''}"
    
    # For Samsung Galaxy models
    samsung_match = re.search(r"(galaxy|samsung)\s*([a-z]+)?\s*(\d+)(?:\s*(plus|ultra|fe))?", message.lower())
    if samsung_match:
        series = samsung_match.group(2) or ""
        model_num = samsung_match.group(3)
        variant = samsung_match.group(4) or ""
        details["model"] = f"Galaxy {series.upper() if series else ''}{model_num}{' ' + variant.capitalize() if variant else ''}"
    
    # Extract repair service type
    repair_keywords = {
        "english": {
            "screen": "screen replacement",
            "battery": "battery replacement",
            "software": "software repairs",
            "unlock": "unlock service",
            "frp": "FRP unlock",
            "icloud": "iCloud unlock",
            "mi account": "Mi account unlock"
        },
        "sinhala": {
            "තිරය": "screen replacement",
            "බැටරිය": "battery replacement", 
            "සොෆ්ට්වෙයාර්": "software repairs",
            "අගුළු": "unlock service",
            "frp": "FRP unlock", 
            "iCloud": "iCloud unlock",
            "mi": "Mi account unlock"
        }
    }
    
    for keyword, service in repair_keywords.get(language, repair_keywords["english"]).items():
        if keyword.lower() in message.lower():
            details["service"] = service
            break
    
    # Extract accessory type
    accessory_keywords = {
        "english": ["charger", "cable", "cover", "case", "glass", "headphone", "earphone", "earbud", "protector"],
        "sinhala": ["චාජර්", "කේබල්", "කවර", "කේස්", "ග්ලාස්", "හෙඩ්ෆෝන්", "ඉයර්ෆෝන්", "ඉයර්බඩ්", "ආරක්ෂක"]
    }
    
    for keyword in accessory_keywords.get(language, accessory_keywords["english"]):
        if keyword.lower() in message.lower():
            details["accessory"] = keyword
            break
    
    return details

def handle_stock_inquiry(message, language):
    """Handle stock inquiries and return stock availability"""
    stock = SHOP_INFO[language]["stock"]
    for item in stock:
        if item.lower() in message.lower():
            quantity = stock[item]
            if quantity > 0:
                if language == "english":
                    return f"We currently have {quantity} units of {item} in stock. Let us know if you'd like to reserve one or need more details!"
                elif language == "sinhala":
                    return f"අපට දැන් {item} එකක {quantity} ඒකම් ඇත. ඔබට එකක් වෙන්කර ගැනීමට හෝ වැඩි විස්තර අවශ්‍ය නම් අපට දන්වන්න!"
                else:  # Singlish
                    return f"Ape stock eke {item} {quantity} units thiyenawa. Oya ekak reserve karanna nam kiyanna!"
            else:
                if language == "english":
                    return f"Unfortunately, we are currently out of stock for {item}. Please check back later or call us for updates."
                elif language == "sinhala":
                    return f"සමාවන්න, {item} සඳහා අපට දැන් ගබඩාවේ තොග නොමැත. කරුණාකර පසුව සොයා බලන්න හෝ අපට අමතන්න."
                else:  # Singlish
                    return f"Sorry, {item} stock eka danne out. Pasuwa balanna or call karanna updates walata."
    # If the item is not found in the stock dictionary
    if language == "english":
        return "Hi there! To find out exactly how many units we have in stock, it's best to call us on 0767410963 / 0768371984 / 0764171984. Our stock changes frequently."
    elif language == "sinhala":
        return "ආයුබෝවන්! අපගේ ගබඩාවේ තොගය පිළිබඳ නිවැරදි තොරතුරු දැනගැනීමට, කරුණාකර 0767410963 / 0768371984 / 0764171984 අමතන්න. අපගේ තොගය නිතරම වෙනස් වේ."
    else:  # Singlish
        return "Hi! Stock details gena sure wenna nam call karanna 0767410963 / 0768371984 / 0764171984. Stock changes frequently."

def get_product_image(category, brand, model):
    """Get image path for a specific product"""
    try:
        if category in PRODUCT_IMAGES:
            if brand.lower() in PRODUCT_IMAGES[category]:
                if model in PRODUCT_IMAGES[category][brand.lower()]:
                    image_path = PRODUCT_IMAGES[category][brand.lower()][model]
                    if os.path.isfile(image_path):
                        return image_path
    except Exception as e:
        print(f"Error getting product image: {e}")
    return None

def get_prompt_by_language(message, state, context, history):
    """Generate language-specific prompts for AI"""
    base_info = SHOP_INFO[state.language]
    
    if state.language == "sinhala":
        return f"""ඔබ සුන් මොබයිල් හොරණ සහකරු ලෙස පාරිභෝගිකයාගේ විමසුමට උදව් කරන්න.

පෙර සංවාදය:
{history}

වත්මන් සාප්පු තොරතුරු:
- ලබාගත හැකි වෙළඳ නාම: {', '.join(base_info['brands'])}
- සේවාවන්: {', '.join(base_info['services'])}
- ස්ථානය: {base_info['address']}
- සම්බන්ධ කරගන්න: {base_info['phone']}

{context}

පාරිභෝගික විමසුම: {message}

පහත කරුණු සලකමින් සිංහල භාෂාවෙන් ප්‍රයෝජනවත් සහ ස්වභාවික ලෙස පිළිතුරු දෙන්න:
1. අපගේ නිෂ්පාදන හා සේවා ගැන නිශ්චිත වන්න
2. නිශ්චිත මිල ගණන් සඳහා සාප්පුව අමතන ලෙස යෝජනා කරන්න
3. තාක්ෂණික ගැටළු සඳහා, පොදු තොරතුරු සපයා සාප්පුවට පැමිණෙන ලෙස දිරිමත් කරන්න
4. පිළිතුරු මිත්‍රශීලී, කෙටි සහ වෘත්තීය විය යුතුය
5. අලුත්වැඩියා සේවා සඳහා වගකීම් ඇති බව සඳහන් කරන්න
6. නිෂ්පාදන යෝජනා කරන්නේ නම්, ජනප්‍රිය මාදිලි 1-2 ක් සඳහන් කරන්න"""
    else:
        return f"""As an AI assistant for Sun Mobile Horana, help the customer with their query.

Previous conversation:
{history}

Current shop context:
- Available brands: {', '.join(base_info['brands'])}
- Services: {', '.join(base_info['services'])}
- Location: {base_info['address']}
- Contact: {base_info['phone']}

{context}

Customer query: {message}

Respond in a helpful and natural way in English, keeping in mind:
1. Be specific about products and services we offer
2. For exact pricing, suggest calling the shop
3. For technical issues, provide general information and encourage visiting the store
4. Keep responses friendly, concise and professional
5. Always mention repair services come with warranties
6. If you're suggesting products, mention 1-2 popular models"""

def get_ai_response(message, state):
    """Get AI response with language-specific responses"""
    try:
        shop_info = SHOP_INFO[state.language]
        
        # Detect intent
        intent = detect_intent(message, state.language)
        
        # Extract product details from message
        product_details = extract_product_details(message, state.language)
        
        # Build conversation history context
        history = ""
        if state.conversation_history:
            last_messages = state.conversation_history[-3:]
            history = "\n".join([f"Customer: {m['message']}\nBot: {m['response']}" for m in last_messages])

        # Build specific context based on intent and extracted details
        specific_context = ""
        
        if intent == "product_inquiry" and "brand" in product_details:
            brand = product_details["brand"]
            models = ", ".join(shop_info["popular_models"].get(brand, ["Various models"]))
            price_range = shop_info["price_ranges"].get(brand, "Various prices")
            specific_context = f"""
Customer is asking about {brand} phones.
Available {brand} models: {models}
Price range: {price_range}
"""
        # ... (rest of the context building remains the same)

        # Generate language-specific prompt
        prompt = get_prompt_by_language(message, state, specific_context, history)
        
        # Get AI response
        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"AI Error: {str(e)}")
        return get_fallback_response(state)

def determine_language(message):
    """Determine the language of the message (Sinhala, English, or Singlish)."""
    sinhala_keywords = ["දුරකථන", "චාජර්", "අලුත්වැඩියා", "ලිපිනය", "අංකය", "වේලාව"]
    singlish_keywords = ["thiyenawa", "karanna", "wenna", "ganna", "eka", "api", "oya", "nam"]
    
    # Check for Sinhala characters
    if any("\u0d80" <= char <= "\u0dff" for char in message):
        return "sinhala"
    
    # Check for Singlish keywords
    if any(keyword in message.lower() for keyword in singlish_keywords):
        return "singlish"
    
    # Default to English if no Sinhala or Singlish patterns are detected
    return "english"

def process_message(message, state):
    """Process user message using AI for natural conversation"""
    try:
        message = message.strip()
        print(f"Processing message: '{message}' in state: {state.current_stage}")

        # Handle reset command
        if message == "#":
            state.reset()
            return MESSAGES["english"]["welcome"]

        # Handle initial language selection menu
        if state.is_first_message:
            state.is_first_message = False
            return MESSAGES["english"]["welcome"]

        # Handle language selection from welcome message
        if state.current_stage == "welcome":
            if message in ["1", "2", "3"]:
                state.language = {
                    "1": "english",
                    "2": "sinhala",
                    "3": "singlish"
                }.get(message, "english")
                state.current_stage = "menu"
                return MESSAGES[state.language]["menu"]
            else:
                return MESSAGES["english"]["welcome"]

        # For subsequent messages, detect language if not already set
        if not state.language or message == "*":  # Add * to change language anytime
            detected_lang = determine_language(message)
            state.language = detected_lang
            return MESSAGES[state.language]["menu"]

        # Rest of message processing
        intent = detect_intent(message, state.language)
        
        # Extract product details
        product_details = extract_product_details(message, state.language)
        
        # Check if this is a product inquiry and get image
        image_path = None
        if "brand" in product_details and "model" in product_details:
            # Determine category based on intent
            category = "phones" if intent == "product_inquiry" else "accessories"
            image_path = get_product_image(category, product_details["brand"], product_details["model"])

        if intent == "stock_inquiry":
            return handle_stock_inquiry(message, state.language)

        ai_response = get_ai_response(message, state)
        state.add_to_history(message, ai_response)

        # Return both response and image path
        return {
            "text": ai_response,
            "image": image_path
        }

    except Exception as e:
        print(f"Error in process_message: {str(e)}")
        print(traceback.format_exc())
        return {"text": MESSAGES[state.language].get("error", "An error occurred. Please try again.")}

def get_fallback_response(state):
    """Get a fallback response when AI fails"""
    if state.language == "sinhala":
        return "සමාවන්න, මට ඔබේ ප්‍රශ්නයට පිළිතුරු දීමට නොහැකි විය. කරුණාකර නැවත උත්සාහ කරන්න හෝ අපගේ දුරකථන අංකය අමතන්න: 0767410963"
    return "I apologize, I couldn't process your request. Please try again or call us at 0767410963 for immediate assistance."    


@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Sun Mobile Horana Conversational Chatbot API!", "status": "running"}), 200


@app.route("/send", methods=["POST"])
def send_message():
    try:
        data = request.json
        number = data.get("number", "").strip()
        message = data.get("message", "").strip()

        # Skip empty messages and status broadcasts
        if not number or not message or 'status@broadcast' in number:
            return jsonify({
                "success": False,
                "error": "Invalid message or broadcast status"
            }), 400

        # Get or create chat state
        if number not in chat_states:
            chat_states[number] = ChatState()
        
        state = chat_states[number]
        
        # Process message
        result = process_message(message, state)
        
        response = {
            "success": True,
            "message": "Message processed",
            "response": result["text"]
        }
        
        # Add image path if available
        if "image" in result and result["image"]:
            response["image"] = result["image"]
        
        return jsonify(response), 200

    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)