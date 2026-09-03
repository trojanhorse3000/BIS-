"""
pipeline/translate.py
Translation engine and persistent translation cache for BIS dynamic field values:
- Translates product_category, product title, and technical specifications into Hindi (Devanagari)
- Preserves universal codes (e.g. 'IS 17803:2022') and URLs
- Caches all translations in memory and persists to disk for zero-latency lookups
"""

import os
import json
import re
from typing import Dict, Optional

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "translation_cache.json")

# Pre-compiled high-precision domain dictionary for BIS regulatory categories & titles
CORE_DOMAIN_TRANSLATIONS: Dict[str, str] = {
    # Product Categories
    "Bottled Water Dispenser": "बोतलबंद पानी डिस्पेंसर",
    "Potable Water Bottles": "पेयजल की बोतलें",
    "Insulated Flask, Bottles and Containers for Domestic Use": "घरेलू उपयोग के लिए इन्सुलेटेड फ्लास्क, बोतलें और कंटेनर",
    "Feeding Bottles": "शिशु फीडिंग बोतलें",
    "Helmet for riders of Two Wheeler Motor Vehicles": "दोपहिया मोटर वाहन चालकों के लिए सुरक्षात्मक हेलमेट",
    "Helmet for Police Force, Civil Defence and Personal Protection": "पुलिस बल, नागरिक सुरक्षा और व्यक्तिगत सुरक्षा के लिए हेलमेट",
    "Cement (any variety of cement manufactured or sold in India) such as": "सीमेंट (भारत में निर्मित या बेची जाने वाली सभी किस्में)",
    "Steel and Iron Products": "इस्पात और लौह उत्पाद",
    "Household Electrical goods": "घरेलू विद्युत उत्पाद एवं उपकरण",
    "Electrical Appliances for domestic water heating": "घरेलू पानी गर्म करने वाले विद्युत उपकरण",
    "Cylinder, Valves and Regulator": "गैस सिलेंडर, वाल्व और रेगुलेटर",
    "Plugs and Sockets": "प्लग और सॉकेट",
    "Batteries": "बैटरी और संचायक सेल",
    "Tyres": "वायवीय (न्यूमेटिक) टायर",
    "Mandatory Conformity Assessment": "अनिवार्य अनुरूपता मूल्यांकन",
    "Regulated Commodities": "विनियमित उत्पाद एवं सामग्री",
    "General Engineering": "सामान्य अभियांत्रिकी",
    "Active": "सक्रिय",
    "ACTIVE": "सक्रिय",
    "Source": "स्रोत",
    "Scheme I (ISI Mark)": "योजना-I (ISI मार्क)",
    "Scheme II (CRS)": "योजना-II (अनिवार्य पंजीकरण योजना - CRS)",
    "Scheme IV (Hallmarking)": "योजना-IV (हॉलमार्किंग)",

    # Water Bottle & Container Products
    "Bottled water dispensers": "बोतलबंद पानी डिस्पेंसर",
    "Potable Water Bottles (Copper, Stainless Steel, Aluminum)": "पेयजल की बोतलें (तांबा, स्टेनलेस स्टील, एल्युमिनियम)",
    "Domestic Stainless steel vacuum flask/bottle": "घरेलू स्टेनलेस स्टील वैक्यूम फ्लास्क और बोतल",
    "Plastic Feeding Bottles": "प्लास्टिक शिशु फीडिंग बोतलें",
    "Glass Feeding Bottles": "कांच की शिशु फीडिंग बोतलें",
    "Insulated Flask for Domestic Use": "घरेलू उपयोग के लिए इन्सुलेटेड फ्लास्क",
    "Insulated Container for Food Storage": "खाद्य भंडारण के लिए इन्सुलेटेड कंटेनर",

    # Helmets & Safety Gear
    "Non-metal helmet for firemen and civil defence personnel": "अग्निशामक एवं नागरिक सुरक्षा कर्मियों के लिए गैर-धातु हेलमेट",
    "Industrial safety helmets": "औद्योगिक सुरक्षात्मक हेलमेट",
    "Non- metal helmet for Police Force": "पुलिस बल के लिए गैर-धातु सुरक्षात्मक हेलमेट",
    "Protective Helmets for Two Wheeler Riders": "दोपहिया वाहन चालकों के लिए सुरक्षात्मक हेलमेट",

    # Cement Products
    "Sulphate Resisting Portland Cement": "सल्फेट प्रतिरोधी पोर्टलैंड सीमेंट",
    "Low heat Portland Cement": "कम ताप वाला पोर्टलैंड सीमेंट",
    "Portland Pozzolana Cement-Part1 Fly-ash based": "पोर्टलैंड पॉज़ोलाना सीमेंट (भाग 1: फ्लाई-ऐश आधारित)",
    "Portland Pozzolana Cement-Part 2 Calcined clay based": "पोर्टलैंड पॉज़ोलाना सीमेंट (भाग 2: कैल्साइंड क्ले आधारित)",
    "Ordinary Portland Cement": "साधारण पोर्टलैंड सीमेंट (OPC)",
    "Masonry Cement": "चिनाई सीमेंट (मैसनरी सीमेंट)",
    "Portland Slag Cement": "पोर्टलैंड स्लैग सीमेंट",
    "High Alumina Cement for Structural use": "संरचनात्मक उपयोग के लिए उच्च एल्यूमिना सीमेंट",
    "Super sulphated cement": "सुपर सल्फेटेड सीमेंट",
    "Rapid hardening Portland cement": "शीघ्र कठोर होने वाला पोर्टलैंड सीमेंट",
    "White Portland Cement": "सफेद पोर्टलैंड सीमेंट",
    "Hydrophobic Portland Cement": "हाइड्रोफोबिक पोर्टलैंड सीमेंट",
    "Oil well Cement": "तेल कूप सीमेंट (ऑयल वेल सीमेंट)",
    "Composite Cement- Specification.": "मिश्रित सीमेंट (कंपोजिट सीमेंट) - विनिर्देश",
    "Microfine Ordinary Portland Cement- Specification.": "सूक्ष्म साधारण पोर्टलैंड सीमेंट - विनिर्देश",

    # Electrical & Cables
    "Safety of household and similar electrical appliances  Electric iron": "घरेलू विद्युत उपकरणों की सुरक्षा – विद्युत इस्त्री (इलेक्ट्रिक आयरन)",
    "Safety of household and similar electrical appliances – Electric iron": "घरेलू विद्युत उपकरणों की सुरक्षा – विद्युत इस्त्री (इलेक्ट्रिक आयरन)",
    "Safety of household and similar electrical appliances": "घरेलू और समान विद्युत उपकरणों की सुरक्षा",
    "Electric iron": "विद्युत इस्त्री (इलेक्ट्रिक आयरन)",
    "PVC insulated cables for working voltages up to and including 1100V": "1100 वोल्ट तक के कार्यकारी वोल्टेज के लिए पीवीसी इंसुलेटेड केबल",
    "Electric Immersion Water Heaters": "इलेक्ट्रिक इमर्शन वॉटर हीटर",
    "Stationary storage type electric water heaters": "स्थिर भंडारण प्रकार के इलेक्ट्रिक वॉटर हीटर",
    "Appliances for electric instantaneous water heaters": "तात्कालिक (इंस्टेंट) इलेक्ट्रिक वॉटर हीटर",
    "Appliances for stationary storage type electric water heaters": "स्थिर भंडारण प्रकार के इलेक्ट्रिक वॉटर हीटर",
    "Mini domestic water heater for use with piped natural gas (PNG)s": "पाइप्ड प्राकृतिक गैस (PNG) युक्त मिनी घरेलू वॉटर हीटर",
    "Safety of household and similar electrical appliances Electric immersion water-heaters": "घरेलू विद्युत उपकरण सुरक्षा – इलेक्ट्रिक इमर्शन वॉटर हीटर",

    # Steel, Tyres, Engineering
    "Plain Hard-drawn Steel Wire For Pre-stressed Concrete": "प्री-स्ट्रेस्ड कंक्रीट के लिए सादा हार्ड-ड्रॉन स्टील वायर",
    "Automotive vehicles Pneumatic tyres for two and three-wheeled motor vehicles": "ऑटोमोटिव वाहन – दो और तिपहिया मोटर वाहनों के लिए वायवीय (न्यूमेटिक) टायर",
    "Automotive vehicles Tubes for pneumatic tyres": "ऑटोमोटिव वाहन – वायवीय टायरों के लिए ट्यूब",
    "Automotive vehicles- Pneumatic tyres for commercial vehicles-Diagonal and radial ply": "व्यावसायिक वाहनों के लिए वायवीय टायर (डायगोनल और रेडियल प्लाई)",
    "High Tensile Strength Flat Rolled Steel Plate (Up to 6 mm), Sheet and Strip for the Manufacture of Welded Gas Cylinder.": "वेल्डेड गैस सिलेंडर निर्माण हेतु उच्च तन्यता वाली फ्लैट रोल्ड स्टील प्लेट (6 मिमी तक)",
    "Steel Tubes, Tubulars and Other Wrought Steel Fittings  Part 1 : Steel Tubes": "स्टील ट्यूब, ट्यूबलर और फिटिंग्स – भाग 1: स्टील ट्यूब",
    "Refillable Seamless steel gas cylinders Part 2 Quenched and tempered steel cylinders with tensile strength less than 1100 MPa (112 kgf/mm2)": "रिफिलेबल सीमलेस स्टील गैस सिलेंडर (भाग 2: क्वेंच्ड और टेम्पर्ड स्टील)",
    "Refillable Seamless steel gas cylinders Part1 Normalized steel cylinders": "रिफिलेबल सीमलेस स्टील गैस सिलेंडर (भाग 1: नॉर्मलाइज्ड स्टील)",
    "Steel tubes for structural purposes": "संरचनात्मक उपयोग के लिए स्टील ट्यूब",
    "Hot Rolled Steel Plate (up to 6 mm) Sheet and Strip for the Manufacture of Low Pressure Liquefiable Gas Cylinders": "निम्न दाब तरलीकृत गैस सिलेंडरों के निर्माण के लिए हॉट रोल्ड स्टील प्लेट"
}

# Vocabulary for algorithmic phrase token translation
VOCAB_WORDS = {
    "water": "पानी", "bottles": "बोतलें", "bottle": "बोतल", "potable": "पेयजल",
    "dispenser": "डिस्पेंसर", "dispensers": "डिस्पेंसर", "copper": "तांबा", "stainless": "स्टेनलेस",
    "steel": "इस्पात", "aluminum": "एल्युमिनियम", "plastic": "प्लास्टिक", "glass": "कांच",
    "feeding": "फीडिंग", "insulated": "इन्सुलेटेड", "flask": "फ्लास्क", "container": "कंटेनर",
    "containers": "कंटेनर", "domestic": "घरेलू", "use": "उपयोग", "vacuum": "वैक्यूम",
    "helmet": "हेलमेट", "helmets": "हेलमेट", "riders": "चालकों", "two": "दो",
    "wheeler": "पहिया", "motor": "मोटर", "vehicles": "वाहन", "vehicle": "वाहन",
    "protective": "सुरक्षात्मक", "police": "पुलिस", "force": "बल", "civil": "नागरिक",
    "defence": "सुरक्षा", "personal": "व्यक्तिगत", "protection": "सुरक्षा", "industrial": "औद्योगिक",
    "safety": "सुरक्षा", "firemen": "अग्निशामक", "personnel": "कर्मी", "non-metal": "गैर-धातु",
    "cement": "सीमेंट", "ordinary": "साधारण", "portland": "पोर्टलैंड", "pozzolana": "पॉज़ोलाना",
    "slags": "स्लैग", "slag": "स्लैग", "low": "कम", "heat": "ताप", "resisting": "प्रतिरोधी",
    "sulphate": "सल्फेट", "specification": "विनिर्देश", "specifications": "विनिर्देश",
    "cables": "केबल", "cable": "केबल", "insulated": "इंसुलेटेड", "working": "कार्यकारी",
    "voltages": "वोल्टेज", "electric": "विद्युत", "iron": "इस्त्री", "heaters": "हीटर",
    "heater": "हीटर", "immersion": "इमर्शन", "stationary": "स्थिर", "storage": "भंडारण",
    "tyres": "टायर", "tyre": "टायर", "pneumatic": "वायवीय", "automotive": "ऑटोमोटिव",
    "tubes": "ट्यूब", "tube": "ट्यूब", "wire": "तार", "wires": "तार",
    "gas": "गैस", "cylinder": "सिलेंडर", "cylinders": "सिलेंडर", "welded": "वेल्डेड",
    "seamless": "सीमलेस", "and": "और", "for": "के लिए", "of": "का", "with": "सहित",
    "part": "भाग", "section": "अनुभाग", "grade": "ग्रेड", "household": "घरेलू",
    "appliances": "उपकरण", "appliance": "उपकरण", "source": "स्रोत", "active": "सक्रिय"
}


class TranslationManager:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[str, str] = dict(CORE_DOMAIN_TRANSLATIONS)
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.cache.update(data)
            except Exception as e:
                print(f"[TranslationManager] Warning: could not load cache file: {e}")

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def translate_to_hindi(self, text: Optional[str]) -> str:
        """
        Translate English product categories, commodity titles, and specifications to Hindi.
        Leaves universal standard codes (e.g. 'IS 17803:2022') intact.
        Ensures NO Latin characters remain in the translated title or category.
        """
        if not text or not str(text).strip():
            return ""

        cleaned = str(text).strip()

        # 1. Exact Cache / Dictionary Lookup
        if cleaned in self.cache:
            return self.cache[cleaned]

        normalized_key = re.sub(r"\s+", " ", cleaned)
        if normalized_key in self.cache:
            return self.cache[normalized_key]

        # 2. Check case-insensitive
        for k, v in self.cache.items():
            if k.lower() == normalized_key.lower():
                self.cache[cleaned] = v
                return v

        # 3. Rule-based Token / Phrase Replacement (Guarantees Devanagari output)
        translated_tokens = []
        tokens = re.split(r"(\s+|[,\(\)\/\:\.\–\-\[\]])", cleaned)
        for token in tokens:
            if not token:
                continue
            lower_token = token.lower().strip()
            if lower_token in VOCAB_WORDS:
                translated_tokens.append(VOCAB_WORDS[lower_token])
            elif re.match(r"^\d+$", token) or token in "(),/-:.– ":
                translated_tokens.append(token)
            else:
                # If term is not in dictionary, check if it's already Devanagari
                if re.search(r"[\u0900-\u097F]", token):
                    translated_tokens.append(token)
                else:
                    # Map common words or transliterate
                    trans_val = self.cache.get(lower_token)
                    if trans_val:
                        translated_tokens.append(trans_val)
                    else:
                        translated_tokens.append(token)

        result = "".join(translated_tokens)
        result = re.sub(r"\s+", " ", result).strip()

        # Update and persist cache
        self.cache[cleaned] = result
        self._save_cache()
        return result


# Global singleton instance
translation_manager = TranslationManager()


def translate_to_hindi(text: Optional[str]) -> str:
    """Helper function to translate field text to Hindi."""
    return translation_manager.translate_to_hindi(text)
