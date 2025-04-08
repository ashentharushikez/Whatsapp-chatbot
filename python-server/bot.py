from asyncio import run
from flask import Flask, request, jsonify
import os
import traceback
import re
from responses import MESSAGES, FAQ_RESPONSES
from dotenv import load_dotenv
from google.generativeai import GenerativeModel



# Load environment variables
load_dotenv()

app = Flask(__name__)

# Store user states
chat_states = {}

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

    def reset(self):
        saved_language = self.language
        self.__init__()
        self.language = saved_language  # Keep the language preference on reset

    def add_to_history(self, message, response):
        """Add message and response to conversation history"""
        self.conversation_history.append({"message": message, "response": response})
        # Keep only last 10 messages for context
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)

# Initialize the AI model
model = GenerativeModel("gemini-1.5-flash")

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
    }
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
            "icloud": "iCloud unlock",
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

def get_ai_response(message, state):
    """Get AI response with better context handling and product knowledge"""
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

        # Build a more specific prompt based on intent and extracted details
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
            # Track that this user has inquired about this product
            if brand not in state.inquired_products:
                state.inquired_products.append(brand)
                
        elif intent == "accessory_inquiry" and "accessory" in product_details:
            accessory = product_details["accessory"]
            accessory_types = shop_info["accessories_details"].get("chargers" if "charg" in accessory.lower() else 
                                                             "headphones" if any(k in accessory.lower() for k in ["headphone", "earphone", "earbud"]) else
                                                             "data_cables" if "cable" in accessory.lower() else
                                                             "back_covers" if any(k in accessory.lower() for k in ["cover", "case"]) else
                                                             "tempered_glass" if any(k in accessory.lower() for k in ["glass", "protector"]) else
                                                             [], [])
            specific_context = f"""
Customer is asking about {accessory}.
Available types: {', '.join(accessory_types)}
We offer warranty on all accessories.
"""
            
        elif intent == "repair_inquiry" and "service" in product_details:
            service = product_details["service"]
            brand = product_details.get("brand", "various brands")
            
            if "screen" in service.lower():
                cost_info = shop_info["repair_costs"]["screen_replacement"].get(brand, 
                          shop_info["repair_costs"]["screen_replacement"]["Others"])
                specific_context = f"""
Customer is asking about screen replacement for {brand}.
Price range for this service: {cost_info}
We use quality replacement parts with warranty.
"""
            elif "battery" in service.lower():
                cost_info = shop_info["repair_costs"]["battery_replacement"].get(brand, 
                          shop_info["repair_costs"]["battery_replacement"]["Others"])
                specific_context = f"""
Customer is asking about battery replacement for {brand}.
Price range for this service: {cost_info}
We use original batteries with warranty.
"""
            else:
                specific_context = f"""
Customer is asking about {service} for {brand}.
We offer professional repair services with warranty.
For exact pricing, suggest calling the shop or visiting in person.
"""
                
        elif intent == "location_inquiry":
            specific_context = f"""
Customer is asking about our location.
Address: {shop_info['address']}
Landmark: In front of the Hall
"""
            
        elif intent == "contact_inquiry":
            specific_context = f"""
Customer is asking about contact information.
Phone numbers: {shop_info['phone']}
Business hours: {shop_info['hours']}
"""
            
        elif intent == "hours_inquiry":
            specific_context = f"""
Customer is asking about business hours.
We are open: {shop_info['hours']}
"""
            
        elif intent == "delivery_inquiry":
            specific_context = f"""
Customer is asking about delivery.
Delivery information: {shop_info['delivery']}
"""
            
        elif intent == "warranty_inquiry":
            specific_context = f"""
Customer is asking about warranty.
We provide standard warranty for all products:
- Mobile phones: 1 year warranty
- Accessories: 3-6 months warranty depending on the item
- Repair services: 1-3 months warranty
"""

        prompt = f"""As an AI assistant for Sun Mobile Horana, help the customer with their query.

Previous conversation:
{history}

Current shop context:
- Available brands: {', '.join(shop_info['brands'])}
- Services: {', '.join(shop_info['services'])}
- Location: {shop_info['address']}
- Contact: {shop_info['phone']}

{specific_context}

Customer query: {message}

Respond in a helpful and natural way in {state.language} language, keeping in mind:
1. Be specific about products and services we offer
2. For exact pricing, suggest calling the shop
3. For technical issues, provide general information and encourage visiting the store
4. Keep responses friendly, concise and professional
5. Always mention repair services come with warranties
6. If you're suggesting products, mention 1-2 popular models

Response:"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"AI Error: {str(e)}")
        return "Sorry, I couldn't process your request. Please try again or provide more details."

def determine_language(message):
    """Determine the language of the message (English or Sinhala)."""
    sinhala_keywords = ["දුරකථන", "චාජර්", "අලුත්වැඩියා", "ලිපිනය", "අංකය", "වේලාව"]
    for keyword in sinhala_keywords:
        if keyword in message:
            return "sinhala"
    return "english"

def process_message(message, state):
    """Process user message using AI for natural conversation"""
    try:
        message = message.strip()
        print(f"Processing message: '{message}' in state: {state.current_stage}")

        # Handle reset command
        if message == "#":
            state.reset()
            return MESSAGES[state.language]["welcome"]

        # Detect language
        state.language = determine_language(message)

        # First time greeting
        if state.is_first_message:
            state.is_first_message = False
            initial_greeting = f"""🌟 Welcome to Sun Mobile Horana! 🌟

I'm your AI assistant. I can help you with:
- Information about phones and accessories
- Repair services
- Exchange offers
- Store location and hours
- Any other questions you have

How can I assist you today?"""
            return initial_greeting

        # Get AI response
        ai_response = get_ai_response(message, state)
        
        # Add to conversation history
        state.add_to_history(message, ai_response)
        
        return ai_response

    except Exception as e:
        print(f"Error in process_message: {str(e)}")
        print(traceback.format_exc())
        return MESSAGES[state.language].get("error", "An error occurred. Please try again.")

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
        number = data.get("number")
        message = data.get("message")
        
        if not number or not message:
            return jsonify({
                "success": False, 
                "error": "Missing number or message"
            }), 400

        # Get or create chat state
        if number not in chat_states:
            chat_states[number] = ChatState()
        
        state = chat_states[number]
        
        # Process message
        response = process_message(message, state)
        
        return jsonify({
            "success": True,
            "message": "Message processed",
            "response": response
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)