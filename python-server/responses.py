# Sinhala, English, and Singlish responses for Sun Mobile chatbot

MESSAGES = {
    "english": {
        "welcome": """🌟 Welcome to Sun Mobile Horana! 🌟
Choose your preferred language:
1 English
2 සිංහල
3 Singlish
[Reply with the number of your choice.]
[Type #reset anytime to start over]""",
        "menu": """Hello! Please select an option:
1 Mobile Phones
2 Phone Accessories
3 Repair Services
4 Contact Us
[Reply with the number. To change language, enter *.]""",
        "stock_available": "We have {quantity} units of {item} in stock. Contact us to reserve!",
        "stock_unavailable": "Sorry, {item} is out of stock. Please check back later.",
        "stock_check": "Please call 0767410963 to check stock availability.",
        "error": "Sorry, an error occurred. Please try again or call 0767410963."
    },
    "sinhala": {
        "welcome": """🌟 සුන් මොබයිල් හොරණ වෙත සාදරයෙන් පිළිගනිමු! 🌟
ඔබට අවශ්‍ය භාෂාව තෝරන්න:
1 English
2 සිංහල
3 Singlish
[ඔබේ තේරීම සඳහා අංකය ඇතුළත් කරන්න.]
[නැවත ආරම්භ කිරීමට #reset ටයිප් කරන්න]""",
        "menu": """ආයුබෝවන්! ඔබට අවශ්‍ය සේවාව තෝරන්න:
1 ජංගම දුරකථන
2 උපාංග
3 අලුත්වැඩියා සේවා
4 අප අමතන්න
[අංකය ඇතුළත් කරන්න. භාෂාව වෙනස් කිරීමට * ඇතුළත් කරන්න.]""",
        "stock_available": "{item} ඒකම් {quantity} ගබඩාවේ ඇත. වෙන්කර ගැනීමට අප අමතන්න!",
        "stock_unavailable": "සමාවන්න, {item} ගබඩාවේ නොමැත. පසුව සොයා බලන්න.",
        "stock_check": "තොග තත්ත්වය දැනගැනීමට 0767410963 අමතන්න.",
        "error": "සමාවන්න, දෝෂයක් ඇති විය. නැවත උත්සාහ කරන්න හෝ 0767410963 අමතන්න."
    },
    "singlish": {
        "welcome": """🌟 Sun Mobile Horana ekata Welcome! 🌟
Language eka thoranna:
1 English
2 සිංහල
3 Singlish
[Number eka reply karanna.]
[Chat eka reset karanna #reset type karanna]""",
        "menu": """Ayubowan! Service eka select karanna:
1 Mobile Phones
2 Accessories
3 Repair Services
4 Contact Us
[Number eka reply karanna. Language change karanna * type karanna.]""",
        "stock_available": "{item} units {quantity} stock eke thiyenawa. Reserve karanna call karanna!",
        "stock_unavailable": "Sorry, {item} stock out. Pasuwa check karanna.",
        "stock_check": "Stock check karanna 0767410963 call karanna.",
        "error": "Sorry, error ekak. Try again or call 0767410963."
    }
}

FAQ_RESPONSES = {
    "english": {
        "default": "Please choose an option from the menu.",
        "warranty": "Phones have a 1-year warranty, accessories 3-6 months.",
        "delivery": "We deliver across Sri Lanka in 1-3 days.",
        "payment": "We accept cash, bank transfers, and digital payments.",
        "business_hours": "Open 9:00 AM to 8:00 PM, seven days a week."
    },
    "sinhala": {
        "default": "කරුණාකර මෙනුවෙන් විකල්පයක් තෝරන්න.",
        "warranty": "දුරකථන සඳහා වසරක වගකීමක්, උපාංග සඳහා මාස 3-6.",
        "delivery": "ලංකාව පුරා දින 1-3 තුළ බෙදාහැරීම.",
        "payment": "මුදල්, බැංකු මාරු, ඩිජිටල් ගෙවීම් පිළිගනිමු.",
        "business_hours": "උදේ 9:00 සිට රාත්‍රී 8:00 දක්වා, සතියේ දින 7."
    },
    "singlish": {
        "default": "Menu eken option ekak select karanna.",
        "warranty": "Phones 1-year warranty, accessories 3-6 months.",
        "delivery": "Lanka purama 1-3 days deliver karanawa.",
        "payment": "Cash, bank transfer, digital payment ok.",
        "business_hours": "9:00 AM to 8:00 PM, satiyata."
    }
}

PRODUCT_IMAGES = {
    "phones": {
        "samsung": {
            "Galaxy S23": "/phones/samsung/s23.jpeg",
            "Galaxy S24": "/phones/samsung/s24.jpeg",
            "Galaxy A54": "/phones/samsung/a54.jpeg"
        },
        "apple": {
            "iPhone 15": "/phones/apple/iphone15.jpeg",
            "iPhone 14": "/phones/apple/iphone14.jpeg",
            "iPhone 13": "/phones/apple/iphone13.jpeg"
        }
    },
    "accessories": {
        "chargers": {
            "Fast Charger": "/accessories/chargers/fast_charger.jpeg",
            "Wireless Charger": "/accessories/chargers/wireless_charger.jpeg"
        },
        "cases": {
            "Silicon Case": "/accessories/cases/silicon_case.jpeg",
            "Leather Case": "/accessories/cases/leather_case.jpeg"
        }
    }
}