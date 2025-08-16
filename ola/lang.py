# Complete Language mappings for OpenSubtitles API compatibility
# Old API (3-letter ISO 639-2) -> New API (ISO 639-1 or extended codes)

LANGUAGE_MAP = {
    # Major languages (your existing mappings + extended)
    "eng": "en",  # English
    "spa": "es",  # Spanish
    "fre": "fr",  # French
    "ger": "de",  # German
    "ita": "it",  # Italian
    "por": "pt-PT",  # Portuguese (Portugal)
    "pob": "pt-BR",  # Portuguese (Brazil)
    "rus": "ru",  # Russian
    "chi": "zh-CN",  # Chinese (Simplified)
    "zht": "zh-TW",  # Chinese (Traditional)
    "jpn": "ja",  # Japanese
    "kor": "ko",  # Korean
    "ara": "ar",  # Arabic
    "hin": "hi",  # Hindi
    "tha": "th",  # Thai
    "vie": "vi",  # Vietnamese
    "ind": "id",  # Indonesian
    "may": "ms",  # Malay
    "fil": "tl",  # Filipino/Tagalog
    # European languages
    "dut": "nl",  # Dutch
    "swe": "sv",  # Swedish
    "nor": "no",  # Norwegian
    "dan": "da",  # Danish
    "fin": "fi",  # Finnish
    "ice": "is",  # Icelandic
    "pol": "pl",  # Polish
    "cze": "cs",  # Czech
    "slo": "sk",  # Slovak
    "hun": "hu",  # Hungarian
    "rum": "ro",  # Romanian
    "bul": "bg",  # Bulgarian
    "hrv": "hr",  # Croatian
    "srp": "sr",  # Serbian
    "slv": "sl",  # Slovenian
    "mac": "mk",  # Macedonian
    "alb": "sq",  # Albanian
    "est": "et",  # Estonian
    "lav": "lv",  # Latvian
    "lit": "lt",  # Lithuanian
    "ukr": "uk",  # Ukrainian
    "bel": "be",  # Belarusian
    "gre": "el",  # Greek
    "tur": "tr",  # Turkish
    "arm": "hy",  # Armenian
    "geo": "ka",  # Georgian
    "aze": "az",  # Azerbaijani
    "kaz": "kk",  # Kazakh
    "uzb": "uz",  # Uzbek
    "tgk": "tg",  # Tajik
    "kir": "ky",  # Kyrgyz
    "mon": "mn",  # Mongolian
    # Middle Eastern and African languages
    "per": "fa",  # Persian/Farsi
    "heb": "he",  # Hebrew
    "kur": "ku",  # Kurdish
    "amh": "am",  # Amharic
    "som": "so",  # Somali
    "swa": "sw",  # Swahili
    "hau": "ha",  # Hausa
    "yor": "yo",  # Yoruba
    "ibo": "ig",  # Igbo
    "afr": "af",  # Afrikaans
    "xho": "xh",  # Xhosa
    "zul": "zu",  # Zulu
    # South Asian languages
    "ben": "bn",  # Bengali
    "guj": "gu",  # Gujarati
    "pan": "pa",  # Punjabi
    "mar": "mr",  # Marathi
    "tel": "te",  # Telugu
    "tam": "ta",  # Tamil
    "kan": "kn",  # Kannada
    "mal": "ml",  # Malayalam
    "ori": "or",  # Odia
    "asm": "as",  # Assamese
    "nep": "ne",  # Nepali
    "sin": "si",  # Sinhala
    "dzo": "dz",  # Dzongkha
    "urd": "ur",  # Urdu
    "pus": "ps",  # Pashto
    "dar": "fa",  # Dari (mapped to Persian)
    # East Asian languages
    "bur": "my",  # Burmese/Myanmar
    "khm": "km",  # Khmer
    "lao": "lo",  # Lao
    # European minority languages
    "cat": "ca",  # Catalan
    "eus": "eu",  # Basque
    "glg": "gl",  # Galician
    "bre": "br",  # Breton
    "wel": "cy",  # Welsh
    "gle": "ga",  # Irish
    "gla": "gd",  # Scottish Gaelic
    "cor": "kw",  # Cornish
    "mlt": "mt",  # Maltese
    "ltz": "lb",  # Luxembourgish
    "fao": "fo",  # Faroese
    "sme": "se",  # Northern Sami
    # Latin languages
    "lat": "la",  # Latin
    # Constructed languages
    "epo": "eo",  # Esperanto
    "ina": "ia",  # Interlingua
    "ido": "io",  # Ido
    # Additional languages
    "haw": "haw",  # Hawaiian
    "mao": "mi",  # Maori
    "tah": "ty",  # Tahitian
    "fij": "fj",  # Fijian
    "ton": "to",  # Tongan
    "sam": "sm",  # Samoan
    # Native American languages
    "nav": "nv",  # Navajo
    "che": "chr",  # Cherokee
    # Sign languages (if supported)
    "sgn": "sgn",  # Sign languages (generic)
    # Special cases and less common languages
    "tib": "bo",  # Tibetan
    "div": "dv",  # Divehi/Maldivian
    "mri": "mi",  # Maori (alternative code)
    "smo": "sm",  # Samoan (alternative)
    "tog": "to",  # Tonga (alternative)
    # Additional European languages
    "frp": "frp",  # Franco-Provençal
    "lad": "lad",  # Ladino
    "roh": "rm",  # Romansh
    "fur": "fur",  # Friulian
    "scn": "scn",  # Sicilian
    "vec": "vec",  # Venetian
    "lmo": "lmo",  # Lombard
    "pms": "pms",  # Piedmontese
    "nap": "nap",  # Neapolitan
    "cos": "co",  # Corsican
    "sar": "sc",  # Sardinian
    # Regional variants (if needed)
    "en-us": "en",  # English (US) - fallback to en
    "en-gb": "en",  # English (GB) - fallback to en
    "fr-ca": "fr",  # French (Canada) - fallback to fr
    "es-mx": "es",  # Spanish (Mexico) - fallback to es
    "de-at": "de",  # German (Austria) - fallback to de
    "de-ch": "de",  # German (Switzerland) - fallback to de
}

# Reverse mapping for converting from new API codes to old API codes
LANGUAGE_MAP_REVERSE = {v: k for k, v in LANGUAGE_MAP.items()}

# Handle special cases in reverse mapping where multiple old codes map to same new code
LANGUAGE_MAP_REVERSE.update(
    {
        "en": "eng",  # Prefer 'eng' over other English variants
        "pt-PT": "por",  # Portuguese (Portugal)
        "pt-BR": "pob",  # Portuguese (Brazil)
        "zh-CN": "chi",  # Chinese (Simplified)
        "zh-TW": "zht",  # Chinese (Traditional)
    }
)

# Language names for display purposes
LANGUAGE_NAMES = {
    # Major languages
    "eng": "English",
    "spa": "Spanish",
    "fre": "French",
    "ger": "German",
    "ita": "Italian",
    "por": "Portuguese",
    "pob": "Portuguese (Brazilian)",
    "rus": "Russian",
    "chi": "Chinese (Simplified)",
    "zht": "Chinese (Traditional)",
    "jpn": "Japanese",
    "kor": "Korean",
    "ara": "Arabic",
    "hin": "Hindi",
    "tha": "Thai",
    "vie": "Vietnamese",
    "ind": "Indonesian",
    "may": "Malay",
    "fil": "Filipino",
    # European languages
    "dut": "Dutch",
    "swe": "Swedish",
    "nor": "Norwegian",
    "dan": "Danish",
    "fin": "Finnish",
    "ice": "Icelandic",
    "pol": "Polish",
    "cze": "Czech",
    "slo": "Slovak",
    "hun": "Hungarian",
    "rum": "Romanian",
    "bul": "Bulgarian",
    "hrv": "Croatian",
    "srp": "Serbian",
    "slv": "Slovenian",
    "mac": "Macedonian",
    "alb": "Albanian",
    "est": "Estonian",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "ukr": "Ukrainian",
    "bel": "Belarusian",
    "gre": "Greek",
    "tur": "Turkish",
    "arm": "Armenian",
    "geo": "Georgian",
    "aze": "Azerbaijani",
    "kaz": "Kazakh",
    "uzb": "Uzbek",
    "tgk": "Tajik",
    "kir": "Kyrgyz",
    "mon": "Mongolian",
    # Middle Eastern and African
    "per": "Persian",
    "heb": "Hebrew",
    "kur": "Kurdish",
    "amh": "Amharic",
    "som": "Somali",
    "swa": "Swahili",
    "hau": "Hausa",
    "yor": "Yoruba",
    "ibo": "Igbo",
    "afr": "Afrikaans",
    "xho": "Xhosa",
    "zul": "Zulu",
    # South Asian
    "ben": "Bengali",
    "guj": "Gujarati",
    "pan": "Punjabi",
    "mar": "Marathi",
    "tel": "Telugu",
    "tam": "Tamil",
    "kan": "Kannada",
    "mal": "Malayalam",
    "ori": "Odia",
    "asm": "Assamese",
    "nep": "Nepali",
    "sin": "Sinhala",
    "dzo": "Dzongkha",
    "urd": "Urdu",
    "pus": "Pashto",
    "dar": "Dari",
    # Southeast Asian
    "bur": "Burmese",
    "khm": "Khmer",
    "lao": "Lao",
    # Regional European
    "cat": "Catalan",
    "eus": "Basque",
    "glg": "Galician",
    "bre": "Breton",
    "wel": "Welsh",
    "gle": "Irish",
    "gla": "Scottish Gaelic",
    "cor": "Cornish",
    "mlt": "Maltese",
    "ltz": "Luxembourgish",
    "fao": "Faroese",
    "sme": "Northern Sami",
    # Other
    "lat": "Latin",
    "epo": "Esperanto",
    "ina": "Interlingua",
    "ido": "Ido",
    "haw": "Hawaiian",
    "mao": "Maori",
    "tah": "Tahitian",
    "fij": "Fijian",
    "ton": "Tongan",
    "sam": "Samoan",
    "nav": "Navajo",
    "che": "Cherokee",
    "sgn": "Sign Language",
    "tib": "Tibetan",
    "div": "Divehi",
}

# Language mapping for SubDL (SubDL uses 2-letter codes like EN, FR, ES)
SUBDL_LANGUAGE_MAP = {
    # Map old OpenSubtitles codes to SubDL language codes
    "eng": "EN",
    "spa": "ES",
    "fre": "FR",
    "ger": "DE",
    "ita": "IT",
    "por": "PT",
    "pob": "BR_PT",  # Brazilian Portuguese
    "rus": "RU",
    "chi": "ZH",
    "zht": "ZH_BG",  # Traditional Chinese (Big5)
    "jpn": "JA",
    "kor": "KO",
    "ara": "AR",
    "hin": "HI",
    "tha": "TH",
    "vie": "VI",
    "ind": "ID",
    "may": "MS",  # Malay
    "fil": "TL",  # Filipino/Tagalog
    "dut": "NL",  # Dutch
    "swe": "SV",  # Swedish
    "nor": "NO",  # Norwegian
    "dan": "DA",  # Danish
    "fin": "FI",  # Finnish
    "pol": "PL",  # Polish
    "cze": "CS",  # Czech
    "hun": "HU",  # Hungarian
    "rum": "RO",  # Romanian
    "bul": "BG",  # Bulgarian
    "hrv": "HR",  # Croatian
    "srp": "SR",  # Serbian
    "ukr": "UK",  # Ukrainian (SubDL uses UK)
    "gre": "EL",  # Greek
    "tur": "TR",  # Turkish
    "per": "FA",  # Persian/Farsi
    "heb": "HE",  # Hebrew
    "cat": "CA",  # Catalan
    "eus": None,  # Basque - not supported by SubDL
    "lat": None,  # Latin - not supported by SubDL
    "slo": "SK",  # Slovak
    "slv": "SL",  # Slovenian
    "est": "ET",  # Estonian
    "lav": "LV",  # Latvian
    "lit": "LT",  # Lithuanian
    "mac": "MK",  # Macedonian
    "alb": "SQ",  # Albanian
    "ben": "BN",  # Bengali
    "bur": "MY",  # Burmese
    "geo": "KA",  # Georgian
    "ice": "IS",  # Icelandic
    "kur": "KU",  # Kurdish
    "mal": "ML",  # Malayalam
    "tam": "TA",  # Tamil
    "tel": "TE",  # Telugu
    "urd": "UR",  # Urdu
    "bel": "BE",  # Belarusian
    "bos": "BS",  # Bosnian
    "aze": "AZ",  # Azerbaijani
}


# Helper functions
def get_new_api_language(old_code):
    """Convert old API 3-letter code to new API code"""
    return LANGUAGE_MAP.get(old_code.lower())


def get_old_api_language(new_code):
    """Convert new API code to old API 3-letter code"""
    return LANGUAGE_MAP_REVERSE.get(new_code.lower())


def get_language_name(old_code):
    """Get display name for language using old API code"""
    return LANGUAGE_NAMES.get(old_code.lower(), old_code.upper())


def is_supported_language(code, api_type="old"):
    """Check if language code is supported"""
    if api_type == "old":
        return code.lower() in LANGUAGE_MAP
    else:
        return code.lower() in LANGUAGE_MAP_REVERSE
