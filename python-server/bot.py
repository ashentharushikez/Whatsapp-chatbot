from flask import Flask, request, jsonify
import os
import traceback
import re
import time
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from responses import MESSAGES, FAQ_RESPONSES, PRODUCT_IMAGES

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
    logger.warning("Missing GOOGLE_API_KEY. AI responses will be limited.")

# Initialize Flask app
app = Flask(__name__)

# Optional: Ensure your image folder exists
IMAGE_FOLDER = os.path.join('static', 'images')
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Store user states
chat_states = {}

# Define shop information
SHOP_INFO = {
    "english": {
        "name": "Sun Mobile Horana",
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "services": ["hardware repairs", "software repairs", "iCloud unlock", "FRP lock removal", "screen replacement"],
        "address": "No.30 Panadura Road, Horana (In front of the Hall)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "hours": "9:00 AM to 8:00 PM, seven days a week",
        "stock": {
            "Samsung Galaxy S23": 10,
            "iPhone 15": 5,
            "Redmi Note 13 Pro": 15,
            "Fast Charger": 20,
            "Bluetooth Earbuds": 25
        }
    },
    "sinhala": {
        "name": "සුන් මොබයිල් හොරණ",
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "services": ["හාඩ්වෙයාර් අලුත්වැඩියා", "සොෆ්ට්වෙයාර් අලුත්වැඩියා", "iCloud අගුළු ඉවත් කිරීම", "FRP අගුළු ඉවත් කිරීම", "තිර ප්‍රතිස්ථාපනය"],
        "address": "අංක 30, පානදුර පාර, හොරණ (හෝල් එක ඉස්සරහ)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "hours": "උදේ 9:00 සිට රාත්‍රී 8:00 දක්වා, සතියේ දින හතම",
        "stock": {
            "Samsung Galaxy S23": 10,
            "iPhone 15": 5,
            "Redmi Note 13 Pro": 15,
            "වේගවත් චාජර්": 20,
            "බ්ලූටූත් ඉයර්බඩ්ස්": 25
        }
    },
    "singlish": {
        "name": "Sun Mobile Horana",
        "brands": ["Samsung", "Apple", "Xiaomi", "Oppo", "Vivo", "Huawei"],
        "services": ["hardware repairs", "software repairs", "iCloud unlock", "FRP unlock", "screen replacement"],
        "address": "No.30 Panadura Road, Horana (Hall eka issaraha)",
        "phone": "0767410963 / 0768371984 / 0764171984",
        "hours": "9:00 AM to 8:00 PM, seven days a week"
    }
}

class ChatState:
    def __init__(self):
        self.current_stage = "welcome"
        self.language = "sinhala"
        self.conversation_history = []
        self.is_first_message = True
        self.last_activity = time.time()

    def reset(self):
        saved_language = self.language
        self.__init__()
        self.language = saved_language

    def add_to_history(self, message, response):
        response_text = response["text"] if isinstance(response, dict) else response
        self.conversation_history.append({"message": message, "response": response_text})
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)
        self.last_activity = time.time()

# Setup Google AI
try:
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Google AI model initialized successfully")
    else:
        model = None
        logger.warning("No API key found, using fallback responses")
except Exception as e:
    logger.error(f"Failed to initialize Google AI model: {e}")
    model = None

def detect_intent(message, language):
    intents = {
        "english": {
            "product_inquiry": [r"do you (have|sell|offer).*?(phone|iphone|samsung|xiaomi)"],
            "accessory_inquiry": [r"do you (have|sell|offer).*?(charger|cable|case|glass|headphone)"],
            "repair_inquiry": [r"(fix|repair|replace).*?(screen|battery|phone|software)"],
            "location_inquiry": [r"(where|what).*?(location|address|shop)"],
            "contact_inquiry": [r"(contact|phone|number)"],
            "hours_inquiry": [r"(when|what time).*?(open|closed|hours)"],
            "stock_inquiry": [r"(do you have|is there|are there).*?in stock"],
        },
        "sinhala": {
            "product_inquiry": [r"(දුරකථන|ෆෝන්|සැම්සං|අයිෆෝන්).*?(තියෙනවද|විකුණනවද)"],
            "accessory_inquiry": [r"(චාජර්|කේබල්|කවර|ග්ලාස්|හෙඩ්ෆෝන්).*?(තියෙනවද|විකුණනවද)"],
            "repair_inquiry": [r"(හදන්න|ප්‍රතිස්ථාපනය).*?(තිරය|බැටරිය|දුරකථනය)"],
            "location_inquiry": [r"(ලිපිනය|ස්ථානය|කොහේද)"],
            "contact_inquiry": [r"(දුරකථන අංකය|අංකය|සම්බන්ධ)"],
            "hours_inquiry": [r"(විවෘත|වසා).*?(වේලාව)"],
            "stock_inquiry": [r"(තිබේද|ඇතිද|ඇවිත්ද)"],
        },
        "singlish": {
            "product_inquiry": [r"(phone|iphone|samsung|xiaomi).*?(thiyenawa|ganna)",r"mata.*?(phone|iphone|samsung|xiaomi).*?(oona|ona|eka)"],
            "accessory_inquiry": [r"(charger|cable|case|glass|headphone).*?(thiyenawa|ganna)"],
            "repair_inquiry": [r"(fix|repair).*?(screen|battery|phone)"],
            "location_inquiry": [r"(where|kohenda).*?(shop|place)"],
            "contact_inquiry": [r"(number|contact|call)"],
            "hours_inquiry": [r"(open|close).*?(time|hours)"],
            "stock_inquiry": [r"(thiyenawa|available).*?(stock)"],
        }
    }
    for intent, patterns in intents.get(language, intents["english"]).items():
        for pattern in patterns:
            if re.search(pattern, message.lower()):
                return intent
    return "general"

def extract_product_details(message, language):
    details = {}
    brands = SHOP_INFO[language]["brands"]
    for brand in brands:
        if brand.lower() in message.lower():
            details["brand"] = brand
            break
    iphone_match = re.search(r"iphone\s*(\d+)(?:\s*(pro|plus|max))?", message.lower())
    if iphone_match:
        model_num = iphone_match.group(1)
        variant = iphone_match.group(2) or ""
        details["model"] = f"iPhone {model_num}{' ' + variant.capitalize() if variant else ''}"
    samsung_match = re.search(r"(galaxy|samsung)\s*([a-z]+)?\s*(\d+)(?:\s*(plus|ultra|fe))?", message.lower())
    if samsung_match:
        series = samsung_match.group(2) or ""
        model_num = samsung_match.group(3)
        variant = samsung_match.group(4) or ""
        details["model"] = f"Galaxy {series.upper() if series else ''}{model_num}{' ' + variant.capitalize() if variant else ''}"
    return details

def handle_stock_inquiry(message, language):
    stock = SHOP_INFO[language]["stock"]
    for item in stock:
        if item.lower() in message.lower():
            quantity = stock[item]
            if quantity > 0:
                return MESSAGES[language]["stock_available"].format(item=item, quantity=quantity)
            else:
                return MESSAGES[language]["stock_unavailable"].format(item=item)
    return MESSAGES[language]["stock_check"]

def get_product_image(category, brand, model):
    base_path = os.path.join(os.getcwd(), "static", "images")
    try:
        if category in PRODUCT_IMAGES:
            if brand.lower() in PRODUCT_IMAGES[category]:
                if model in PRODUCT_IMAGES[category][brand.lower()]:
                    relative_path = PRODUCT_IMAGES[category][brand.lower()][model]
                    image_path = os.path.join(base_path, relative_path.lstrip("/"))
                    if os.path.isfile(image_path):
                        return relative_path
    except Exception as e:
        logger.error(f"Error getting product image: {e}")
    return None

def get_prompt_by_language(message, state, context, history):
    base_info = SHOP_INFO[state.language]
    if state.language == "sinhala":
        return f"""ඔබ සුන් මොබයිල් හොරණ සහකරු ලෙස පාරිභෝගිකයාගේ විමසුමට උදව් kරන්න.
පෙර සංවාදය: {history}
වත්මන් සාප්පු තොරතුරු:
- වෙළඳ නාම: {', '.join(base_info['brands'])}
- සේවා: {', '.join(base_info['services'])}
- ලිපිනය: {base_info['address']}
- දුරකථන: {base_info['phone']}
{context}
විමසුම: {message}
සිංහලෙන් මිත්‍රශීලී, කෙටි, වෘත්තීය පිළිතුරු දෙන්න."""
    else:
        return f"""You are an assistant for Sun Mobile Horana, helping with customer queries.
Previous conversation: {history}
Current shop info:
- Brands: {', '.join(base_info['brands'])}
- Services: {', '.join(base_info['services'])}
- Address: {base_info['address']}
- Phone: {base_info['phone']}
{context}
Query: {message}
Respond in {state.language}, keeping answers friendly, concise, and professional."""

def get_ai_response(message, state):
    try:
        shop_info = SHOP_INFO[state.language]
        intent = detect_intent(message, state.language)
        product_details = extract_product_details(message, state.language)
        history = "\n".join([f"Customer: {m['message']}\nBot: {m['response']}" for m in state.conversation_history[-3:]])
        specific_context = ""
        if intent == "product_inquiry" and "brand" in product_details:
            brand = product_details["brand"]
            specific_context = f"Customer is asking about {brand} phones."
        prompt = get_prompt_by_language(message, state, specific_context, history)
        if model:
            response = model.generate_content(prompt)
            return response.text.strip()
        else:
            return FAQ_RESPONSES[state.language].get(intent, FAQ_RESPONSES[state.language]["default"])
    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        return MESSAGES[state.language]["error"]

def determine_language(message):
    if any("\u0d80" <= char <= "\u0dff" for char in message):
        return "sinhala"
    singlish_keywords = ["thiyenawa", "karanna", "eka", "api", "oya"]
    if any(keyword in message.lower() for keyword in singlish_keywords):
        return "singlish"
    return "english"

from flask import request

def process_message(message, state):
    try:
        message = message.strip()
        logger.info(f"Processing message: '{message}' in stage: {state.current_stage}")

        # Reset command
        if message == "*":
            state.reset()
            return {"text": MESSAGES["english"]["welcome"]}

        # First message
        if state.is_first_message:
            state.is_first_message = False
            return {"text": MESSAGES["english"]["welcome"]}

        # Language selection
        if state.current_stage == "welcome":
            if message in ["1", "2", "3"]:
                state.language = {"1": "english", "2": "sinhala", "3": "singlish"}.get(message, "english")
                state.current_stage = "menu"
                return {"text": MESSAGES[state.language]["menu"]}
            return {"text": MESSAGES["english"]["welcome"]}

        # Main menu selection
        if state.current_stage == "menu":
            if message in ["1", "2", "3", "4"]:
                state.current_stage = "interaction"
                menu_responses = {
                    "1": "Please tell me which phone you're interested in. We have Samsung, iPhone, Xiaomi, and more.",
                    "2": "We have various accessories including chargers, cases, and screen protectors. What are you looking for?",
                    "3": "What type of repair service do you need? We handle both hardware and software issues.",
                    "4": "You can reach us at:\n📞 0767410963 / 0768371984\n📍 No.30 Panadura Road, Horana"
                }
                return {"text": menu_responses[message]}
            return {"text": MESSAGES[state.language]["menu"]}

        # Product inquiries and other interactions
        intent = detect_intent(message, state.language)
        product_details = extract_product_details(message, state.language)

        if "iphone" in message.lower() or "apple" in message.lower():
            response_text = ("Here are our iPhone models:\n"
                           "- iPhone 15 series (starting from Rs. 275,000)\n"
                           "- iPhone 14 series (starting from Rs. 225,000)\n"
                           "- iPhone 13 series (starting from Rs. 195,000)\n"
                           "Which model would you like to know more about?")
            image_path = "/static/images/phones/apple/iphone15.jpeg"
            return {
                "text": response_text,
                "image": request.host_url.rstrip('/') + image_path if os.path.exists(os.path.join(app.static_folder, "images/phones/apple/iphone15.jpeg")) else None
            }

        if intent == "product_inquiry" and product_details:
            brand = product_details.get("brand")
            model = product_details.get("model")
            response_text = get_ai_response(message, state) or f"Please tell me more about which {brand} model you're interested in."
            
            image_path = get_product_image("phones", brand, model) if brand and model else None
            response = {"text": response_text}
            if image_path:
                response["image"] = request.host_url.rstrip('/') + image_path

            return response

        # Default response
        response_text = get_ai_response(message, state) or FAQ_RESPONSES[state.language]["default"]
        return {"text": response_text}

    except Exception as e:
        logger.error(f"Error in process_message: {str(e)}\n{traceback.format_exc()}")
        return {"text": MESSAGES.get(getattr(state, 'language', 'english'), MESSAGES["english"])["error"]}


@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Sun Mobile Horana Chatbot API!", "status": "running"}), 200

@app.route("/send", methods=["POST"])
def send_message():
    try:
        data = request.json
        number = data.get("number", "").strip()
        message = data.get("message", "").strip()

        if not number or not message or number == 'status@broadcast':
            return jsonify({
                "success": True,
                "message": "Ignoring broadcast or invalid message",
                "response": ""
            }), 200

        if number not in chat_states:
            chat_states[number] = ChatState()
        
        state = chat_states[number]
        result = process_message(message, state)
        
        if not result:
            return jsonify({
                "success": True,
                "message": "Message processed",
                "response": MESSAGES[state.language]["error"]
            }), 200

        response = {
            "success": True,
            "message": "Message processed",
            "response": result.get("text", MESSAGES[state.language]["error"])
        }
        
        if "image" in result and result["image"]:
            response["image"] = result["image"]
        
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "success": True,
            "message": "Error processing message",
            "response": "Sorry, there was an error. Please try again."
        }), 200

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    user_message = data.get('message', '').lower()

    # Example product images
    product_images = {
        "iphone 15": "static/images/phones/samsung/iphone15.jpeg",
        "samsung s24": "static/images/phones/samsung/s24.jpeg",
        # Add more if needed
    }

    # Flag for "does user want an image?"
    wants_image = 'image' in user_message or 'images' in user_message

    detected_product = None
    for product in product_images:
        if product in user_message:
            detected_product = product
            break

    # CASE 1 → User wants image + product is detected
    if wants_image and detected_product:
        image_path = product_images[detected_product]
        image_url = f'http://127.0.0.1:5000/{image_path}'

        return jsonify({
            "success": True,
            "response": f"Here is an image of {detected_product.title()} 📷",
            "image": image_url
        })

    # CASE 2 → User asks about iPhone 15 but not explicitly for image
    elif 'iphone 15' in user_message:
        return jsonify({
            "success": True,
            "response": "We do stock iPhones, but currently, we don't have the iPhone 15 in stock. Could you tell me if you're interested in other iPhone models or perhaps a different brand, like Samsung or Xiaomi? We can help you find a great alternative."
        })

    # CASE 3 → Default fallback
    else:
        return jsonify({
            "success": True,
            "response": "I'm here to help! Please tell me which phone model or brand you're interested in."
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    os.makedirs(os.path.join(os.getcwd(), "static", "images"), exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)