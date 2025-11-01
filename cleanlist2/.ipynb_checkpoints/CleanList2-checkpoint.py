# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                                                        ---- CleanList App: Shop Smarter. Eat Cleaner. ----
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Core Libraries ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#CleanList App: Build grocery lists (or upload picture) and produce an alternative list with a per-item and per-list "CleanScore".
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from uuid import uuid4
import io, re, unicodedata, torch, base64, time, pandas as pd, streamlit as st
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sentence_transformers import CrossEncoder
import matplotlib.pyplot as plt, seaborn as sns, plotly.express as px, textwrap
import streamlit as st
from uuid import uuid4


# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Heuristic CleanScore engine ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
GMO_INGREDIENTS = [
    "corn", "corn syrup", "corn starch", "high fructose corn syrup",
    "soy", "soy lecithin", "soy protein", "soybean oil", "canola oil", "corn oil",
    "canola", "canola oil", "cottonseed oil", "sugar beets", "refined sugar",
    "papaya (ringspot virus-resistant)", "summer squash (zucchini, yellow squash)",
    "potato (innate varieties)", "apple (Arctic varieties)","pink pineapple", 
    "alfalfa", "eggplant (BARI Bt Begun varieties)", "corn syrup", "high fructose corn syrup", "soybean oil", 
    "vegetable oil", "rapeseed oil", "soy protein isolate", "wheat flour", 
    "refined flour", "white flour", "enriched flour", "sugar", "glucose", 
    "fructose", "dextrose", "maltodextrin", "papaya", "summer squash", "potato", 
    "apple", "pink pineapple", "cottonseed oil","cane sugar"
]

ARTIFICIAL_INGREDIENTS = [
    "artificial flavor", "artificial color",
    "red 40", "blue 1", "yellow 5", "yellow 6", "green 3",
    "sodium benzoate", "potassium benzoate",
    "butylated hydroxyanisole (BHA)", "butylated hydroxytoluene (BHT)",
    "monosodium glutamate (MSG)",
    "sodium nitrite", "sodium nitrate",
    "propyl gallate", "propylene glycol",
    "sorbitol", "sucralose", "aspartame", "acesulfame potassium",
    "calcium propionate", "benzoic acid",
    "dimethylpolysiloxane", "polysorbate 80", "polysorbate 60",
    "carboxymethylcellulose", "cellulose gum",
    "disodium inosinate", "disodium guanylate",
    "aluminum salts", "synthetic vanillin", 
    # Sugars/Syrups
    "corn syrup", "high fructose corn syrup", "invert sugar", "glucose", "dextrose", "fructose", "maltodextrin",
    # Trans fats
    "partially hydrogenated", "hydrogenated", "trans fat", "shortening",
    # Preservatives
    "bht", "bha", "tbhq", "propyl gallate", "sodium benzoate", "potassium sorbate", "disodium phosphate", "phosphate",
    # MSG
    "monosodium glutamate", "msg",
    # Colors
    "red 40", "yellow 5", "yellow 6", "blue 1", "blue 2", "caramel color",
    # Nitrites/Nitrates
    "sodium nitrite", "sodium nitrate", "nitrite", "nitrate",
    # Emulsifiers/Solvents
    "polysorbate 80", "propylene glycol", "titanium dioxide",
    # Bromated flours
    "potassium bromate", "bromated",
    # Sweeteners
    "aspartame", "sucralose", "acesulfame", "saccharin",
    # Gums
    "carboxymethylcellulose", "carrageenan", "xanthan gum", "guar gum",
    # Artificial flavors/colors
    "artificial flavor", "artificial flavours", "artificial color", "artificial colour", "natural flavors", "natural flavour"
]

HEALTHY_INGREDIENTS = [
    # Whole Food-Based Ingredients
    "oats", "quinoa", "brown rice", "farro", "millet", "barley",
    "lentils", "chickpeas", "black beans", "edamame",
    "almonds", "walnuts", "chia seeds", "flaxseeds", "sunflower seeds", "pumpkin seeds",
    "dates", "raisins", "apricots", "figs", "goji berries",
    "kale", "spinach", "sweet potato", "beetroot", "carrots", "peas",
    "apple", "banana", "blueberry", "mango", "pineapple",

    # Natural Flavor Enhancers & Seasonings
    "turmeric", "cinnamon", "ginger", "garlic", "basil", "oregano", "cumin",
    "sea salt", "apple cider vinegar", "balsamic vinegar", "lemon juice", "lime juice",

    # Clean Dairy & Alternatives
    "greek yogurt", "almond milk", "oat milk", "cashew milk",
    "feta cheese", "goat cheese", "part-skim mozzarella",

    # Functional Additives
    "honey", "maple syrup", "monk fruit", "stevia",
    "psyllium husk", "inulin", "chicory root fiber",
    "lactobacillus", "bifidobacterium",
    "pea protein", "whey isolate", "hemp protein",
    "calcium carbonate","soy protein isolate"
]
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Heuristic CleanScore engine ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*

# --- Predefined Grocery Database  ---
grocery_item_db = {
    "Oats_brand1": ["organic oats", "cane sugar", "honey", "almonds"],
    "Oats_brand2": ["organic oats", "cane sugar", "honey"],
    "Oats_brand3": ["organic oats", "cane sugar"],
    "Oats_brand4": ["honey", "almonds"],
    "nola_Quaker1": ["honey"],
    "nola_Quaker2": ["organic oats", "cane sugar", "honey"],
    "Quaker": ["organic oats"],
    "Justin's": ["roasted peanuts", "salt", "palm oil"],
    "noodles_brand1": ["wheat flour", "salt", "monosodium glutamate", "vegetable oil"],
    "noodles_brand2": ["monosodium glutamate", "vegetable oil"],
    "noodles_brand3": ["wheat flour", "salt"],
    "Almond Breeze": ["filtered water", "almonds", "calcium carbonate", "vitamin D2"],
    "protein_brand1": ["soy protein isolate", "chocolate chips", "sugar", "natural flavors"],
    "protein_brand2": ["soy protein isolate", "natural flavors"]
}

grocery_brands_db = {
     "granola": ['Oats_brand1','Oats_brand2','Oats_brand3','Oats_brand4'],
     "nola": ['nola_Quaker1','nola_Quaker2'],
     "ola": ['Quaker'],
     "peanut butter": ["Justin's"],
     "instant noodles": ["noodles_brand1","noodles_brand2","noodles_brand3"],
     "almond milk": ["Almond Breeze"],
     "protein bar": ["protein_brand1","protein_brand2"]
}


# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Global Functions ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#///////////////////////   ******** Funciton for Text Normalization: normalizes unicode and collapses whitespace ********
def normalize_text(s: str) -> str: 
    if not isinstance(s, str): 
        return ""                         # Type Safety - prevents crashes if a non-string sneaks in.
    s = s.lower() 	                      # Lowercase
    s = unicodedata.normalize("NFKC", s)  # Unicode Normalization
    s = re.sub(r"\s+", " ", s).strip()    # Collapse Whitespace
    s = re.sub(r"[^\w\s]", "", s)         # Punctuation removal
    return s 

#///////////////////////   ******** Function to convert Logo to base64 so it can be embedded directly ********
def convert_logo_to_base64(logo_file_path):
    with open(logo_file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()
    
#///////////////////////   ******** Function for ingredient color map ********    
def ingredient_color_map(ingredient):
    if ingredient in GMO_INGREDIENTS or ingredient in ARTIFICIAL_INGREDIENTS:
        return f"<span style='color:red; font-weight:bold;'>{ingredient}</span>"
    else:
        return ingredient  # default color

# ///////////////////////   ******** Function to flash message on UX/UI ******** 
def flash_message(message, msg_type, duration=2):
    # Create placeholders 
    msg_box = st.empty()
    css_box = st.empty()

    # Show the message
    if msg_type == "info":
        msg_box.info(message)
    elif msg_type == "success":
        msg_box.success(message)
    elif msg_type == "warning":
        msg_box.warning(message)
    elif msg_type == "error":
        msg_box.error(message)
    else:
        msg_box.markdown(message)

    # Inject fade-out CSS
    css_box.markdown(f"""
        <style>
        @keyframes fadeOut {{
            from {{ opacity: 1; }}
            to {{ opacity: 0; }}
        }}
        .stAlert {{
            animation: fadeOut {duration}s ease forwards;
        }}
        </style>
    """, unsafe_allow_html=True)

    # Wait for animation to finish, then clear
    time.sleep(duration + 0.1)
    msg_box.empty()
    css_box.empty()

#/////////////////////// ******** Function for creating CleanList ********
def create_CleanList(input_value):
    item_text = normalize_text(input_value)

    for key, values in grocery_brands_db.items():
        key_normalized = normalize_text(key)

        # Use full match instead of partial match
        if item_text == key_normalized:
            top_brand_name = values[0].strip()

            for k in grocery_item_db:
                if normalize_text(k) == normalize_text(top_brand_name):
                    return grocery_item_db.get(k, "Item Not Available")

    return input_value

# ///////////////////////   ******** Function to compute a bounded CleanScore ******** 
def score_item(item: str, ingredients: Optional[str]) -> Tuple[int, Dict[str, List[str]]]:
    base = 100
    item_text = normalize_text(item) 
    ing_text = " ".join(normalize_text(i) for i in ingredients or [item]) #normalize_text(ingredients or item)
    matched = {"GMO": [], "AI": [], "both": []}
    
    # GMO signals 
    for kw in GMO_INGREDIENTS: 
        if kw in ing_text: 
            matched["GMO"].append(kw) 
            
    # AI signals  
    for kw in ARTIFICIAL_INGREDIENTS: 
        if kw in ing_text: 
            matched["AI"].append(kw) 
     
    # Both GMO and AI signals 
    for kw in GMO_INGREDIENTS and ARTIFICIAL_INGREDIENTS: 
        if kw in ing_text: 
            matched["both"].append(kw)    

    # Scoring logic (bounded) 
    score = base 
    score -= 7 * len(matched["GMO"])                  # per unique positive 
    score -= 14 * len(matched["AI"])              # per unique moderate negative 
    score -= 30 * len(matched["both"])               # per unique strong negative 
    score = max(0, min(100, int(round(score)))) 
    return score, matched

#///////////////////////   ******** Function for scoring all items on the grocery list ********
def score_CleanList(item):
    item_text = normalize_text(item)
    if item in grocery_item_db:
        ingredients = grocery_item_db[item_text]
        brand_name = grocery_brands_db[item_text]
 
        #Calculate CleanScore
        final_score = score_item(item, ingredients) #score_item(item, result['ingredients'])
    
        # CleanScore color map
        if final_score[0] < 50:
            color = "red"
        elif final_score[0] < 80:
            color = "orange"  # yellow can be hard to read on white background
        else:
            color = "green"
     
    else:
        st.error("Item not found.")
    return final_score  

#///////////////////////   ******** Function for highlighting ingredient list ********
def color_code_ingredients(ingredients, CleanScore):
    if ingredients == "Igredients Not Available" or CleanScore == "CleanScore Not Available":
        return CleanScore, ingredients
    
    # Determine color based on number
    if CleanScore < 60:
        color = "red"
        bold = True
    elif CleanScore < 80:
        color = "orange"
        bold = False
    else:
        color = "green"
        bold = False

     # Format number
    if bold:
        styled_number = f'<span style="color:{color}; font-weight:bold;">{CleanScore}</span>'
    else:
        styled_number = f'<span style="color:{color};">{CleanScore}</span>'
    formatted_ingredients = []
    for item in ingredients:
        formatted_ingredient = ingredient_color_map(item)
        formatted_ingredients.append(formatted_ingredient)
    return styled_number, formatted_ingredients

#///////////////////////   ******** Function for Defensive Flattening ********
def flatten(lst):
    return [item for sublist in lst for item in (sublist if isinstance(sublist, list) else [sublist])]

# ---------- Function for Checkbox: "Select All" ----------
def _on_select_all_changed():
    val = st.session_state["select_all"]
    for it in st.session_state.item_list:
        st.session_state[f"sel_{it['id']}"] = val

# ---------- Callback for Enter key ----------
def trigger_search_callback():
    st.session_state.trigger_search = True
    
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                          ✈️🏨💰💕🌴🏝️💎🌺⇒👥💡📊👉💳🧱 🛒 📝 🧪 🧺🎷🛒 📝  ---- Streamlit UI ---- 📍✅ 📋 🧼 🍑 🔐📸🔍🧾🧩🧑‍💻🎯➡️🎥🌊🌅✨                          
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*

#///////////////////////  ******** Header design ********
# ---------- Page Config ----------
st.set_page_config(
    page_title="CleanList",
    page_icon="🍑",
#    page_icon="favicon-16x16.png"
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    /* Full-width centered logo */
    .center-logo {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .center-logo img {
        max-width: 300px;
        height: auto;
    }

    /* Sticky header */
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 999;
        padding: 0.5rem 1rem;
        border-bottom: 1px solid #eee;
    }

    /* Responsive layout */
    @media (max-width: 768px) {
        .center-logo img {
            max-width: 200px;
        }
        .sticky-header h1 {
            font-size: 1.5rem;
        }
    }

    /* Remove default padding */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Logo ----------
st.markdown("""
    <style>
     .responsive-logo {
        max-width: 250px;
        height: auto;
    }

    @media (max-width: 768px) {
        .responsive-logo {
            max-width: 180px;
        }
    }
    .sticky-header {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 999;
        padding: 0.55rem 1rem;
        border-bottom: 1px solid #eee;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)


# Load and encode background pic
with open("banner2.jpg", "rb") as f:
    bg_data = base64.b64encode(f.read()).decode()

# Load and encode logo pic
with open("CleanList logo.png", "rb") as f:
    logo_data = base64.b64encode(f.read()).decode()

# Inject custom CSS
st.markdown(f"""
    <style>
        .top-banner {{
            background-image: url("data:image/png;base64,{bg_data}");
            background-size: cover;
            background-position: center;
            padding: 3rem 1rem;
            text-align: center;
            width: 100%;
            position: sticky;
            top: 0;
            z-index: 999;
        }}
        .sticky-header h1 {{
            font-family: 'Inter', sans-serif;
            font-size: 6vw;
            margin: 0;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
        }}
        .responsive-logo {{
            max-width: 250px;
            height: auto;
            margin-bottom: 1rem;
        }}
        @media (max-width: 768px) {{
            .sticky-header h1 {{
                font-size: 8vw;
            }}
        }}
    </style>

    <div class="top-banner">
        <a href="http://192.168.1.77:8501" target="_blank">
            <img src="data:image/png;base64,{logo_data}" class="responsive-logo">
        </a>
    </div>
""", unsafe_allow_html=True)

# ---------- Button Row ----------
st.markdown("""
<style>
/* Reduce column gap on desktop */
div[data-testid="stHorizontalBlock"] {
    gap: 0.5rem !important;
}

/* Stack columns vertically on mobile */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        align-items: center !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------- Main Content ----------
#  Session Flags: Initialize states 
if "item_list" not in st.session_state:
    st.session_state.item_list = []
if "select_all" not in st.session_state:
    st.session_state.select_all = False
if "editing" not in st.session_state:
    st.session_state.editing = False
if "just_interacted" not in st.session_state:
    st.session_state.just_interacted = False
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = False
if "prefill_input" in st.session_state:
    st.session_state.add_item_input = st.session_state.prefill_input
    del st.session_state.prefill_input
if "show_create_button" not in st.session_state:
    st.session_state.show_create_button = False
if "trigger_search" not in st.session_state:
    st.session_state.trigger_search = False
if "suggestion_locked" not in st.session_state:
    st.session_state.suggestion_locked = False
if "show_create_cleanlist_button" not in st.session_state:
    st.session_state.show_create_cleanlist_button = False
if "manual_search" not in st.session_state:
    st.session_state.manual_search = False

import streamlit as st
from uuid import uuid4

# ---------- Prefill logic ----------
if "prefill_input" in st.session_state:
    st.session_state.add_item_input = st.session_state.prefill_input
    del st.session_state.prefill_input
    
if st.session_state.get("clear_input", False):
    st.session_state.add_item_input = ""
    st.session_state.clear_input = False
    
if not st.session_state.editing:    
    # ---------- Input + Search Form ----------
    with st.form("search_form", clear_on_submit=False):
        st.text_input(
            "Add an item to your list",
            key="add_item_input",
            placeholder="e.g. Granola"
        )
        submitted = st.form_submit_button("Search Item")
    
    if submitted:
        typed = st.session_state.get("add_item_input", "").strip().lower()
        if not typed:
            flash_message("No item entered.", msg_type="warning", duration=2)
        else:
            st.session_state.trigger_search = True
            st.session_state.manual_search = True
            st.session_state.suggestion_locked = False
            st.session_state.last_typed = typed
            st.rerun()
    
    # ---------- Suggestion Matching ----------
    typed = st.session_state.get("add_item_input", "").strip().lower()
    
    if not st.session_state.get("suggestion_locked", False):
        if typed and typed != st.session_state.get("last_typed", ""):
            st.session_state.last_typed = typed
    
    typed_for_match = st.session_state.get("last_typed", "")
    matches = [brand for brand in grocery_brands_db if typed_for_match and typed_for_match in brand.lower()]

# ---------- Suggestion Rendering ----------
if not st.session_state.editing and st.session_state.trigger_search and matches:
    st.markdown("#### Choose from the following")
    for match in matches:
        match_lower = match.lower()
        match_index = match_lower.find(typed_for_match)
        highlighted = (
            f"{match[:match_index]}"
            f"<span style='background-color:#ffd700; font-weight:bold;'>"
            f"{match[match_index:match_index+len(typed_for_match)]}</span>"
            f"{match[match_index+len(typed_for_match):]}"
        )

        st.markdown(f"<div style='margin-top:-10px;'>{highlighted}</div>", unsafe_allow_html=True)

        if st.button(match, key=f"suggestion_{match}"):
            st.session_state.prefill_input = match
            st.session_state.show_create_button = True
            st.session_state.suggestion_locked = True
            st.session_state.manual_search = False
            st.rerun()

    if st.button("Clear suggestions"):
        st.session_state.trigger_search = False
        st.session_state.last_typed = ""
        st.session_state.show_create_button = False
        st.session_state.suggestion_locked = False
        st.session_state.manual_search = True
        st.rerun()

# ---------- Add to List ----------
if st.session_state.get("show_create_button", False) and not st.session_state.editing:
    if st.button("Add to list"):
        input_value = st.session_state.get("add_item_input", "").strip()
        normalized_input = input_value.lower()

        if not input_value:
            flash_message("Please enter an item before adding.", msg_type="warning", duration=2)
        elif input_value not in grocery_brands_db:
            flash_message(f"'{input_value}' not in database.", msg_type="warning", duration=2)
        else:
            existing_labels = [it["label"].strip().lower() for it in st.session_state.item_list]
            if normalized_input in existing_labels:
                flash_message(f"'{normalized_input}' is already in your CleanList.", msg_type="warning", duration=2)
            else:
                st.session_state.item_list.append({
                    "id": f"it_{uuid4().hex}",
                    "label": input_value
                })
                st.session_state.clear_input = True
                st.session_state.last_typed = ""
                st.session_state.trigger_search = False
                st.session_state.suggestion_locked = False
                st.session_state.show_create_button = False
                st.session_state.show_create_cleanlist_button = True
                st.success(f"Added: {input_value}")
                st.rerun()  

# ---------- Button: Edit List (toggle) ----------
col1, col2 = st.columns([1, 1])
if not st.session_state.editing and st.session_state.item_list:
    with col2:
        if st.button("✏️ Edit List"):
            st.session_state.editing = True
            st.session_state.just_interacted = True
            st.session_state.app_initialized = True
            st.rerun()  # 🔁 Force immediate UI update
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Editing UI (only when editing) ----------
if st.session_state.editing:
    if st.session_state.item_list:
        st.checkbox("Select All", key="select_all", on_change=_on_select_all_changed)
        st.markdown("### 🧺 Select items to remove:")
        for i, it in enumerate(st.session_state.item_list, 1):
            st.checkbox(f"{i}. {it['label']}", key=f"sel_{it['id']}")
    else:
        st.markdown("Your CleanList is empty. Nothing to edit.")

    # ---------- Button: "Remove Selected Items" ----------
    if st.button("🗑️ Remove Selected Items"):
        st.session_state.just_interacted = True
        selected_ids = [it["id"] for it in st.session_state.item_list if st.session_state.get(f"sel_{it['id']}", False)]
        if selected_ids:
            st.session_state.item_list = [it for it in st.session_state.item_list if it["id"] not in selected_ids]
            for sid in selected_ids:
                st.session_state.pop(f"sel_{sid}", None)
            flash_message(f"Removed: {len(selected_ids)} item(s)", msg_type="success", duration=1)
            st.session_state.app_initialized = True
            if not st.session_state.item_list:
                st.session_state.editing = False
            st.rerun()
        else:
            flash_message("No items selected for removal.", msg_type="warning", duration=1)

    # ---------- Button: "Done Editing" ----------
    if st.button("✅ Done Editing"):
        st.session_state.editing = False
        st.session_state.just_interacted = True
        st.session_state.app_initialized = True
        st.rerun()
            
# ---------- Current Items  List (always visible) ----------
if st.session_state.item_list and not st.session_state.editing:
    st.markdown("🧪 Current Items:")
    for i, it in enumerate(st.session_state.item_list, 1):
        st.markdown(f"{i}. {it['label']}")
        
    # ---------- Button: "Create My CleanList" (explicit action) ----------
if not st.session_state.editing and st.session_state.get("show_create_cleanlist_button", False):
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    create_clicked = st.button("🚀 Create My CleanList!")
    if create_clicked:
        st.session_state.just_interacted = True

        if not st.session_state.item_list:
            flash_message("Your list is empty. Add items before creating your CleanList.", msg_type="warning", duration=2)
        else:
            # ✅ Define number generator
            def generate_sleek_numbers(n):
                circled_base = ord("①")
                circled_limit = ord("⑳")
                sleek_numbers = []
                for i in range(n):
                    if circled_base + i <= circled_limit:
                        sleek_numbers.append(chr(circled_base + i))
                    else:
                        sleek_numbers.append(f"🔢{i+1}")
                return sleek_numbers

            st.success("Your CleanList is ready below!")

            # 🍑 Glossy CleanList Header (centered)
            st.markdown(
                """
                <style>
                @keyframes shine {
                    0% {background-position: -200px;}
                    100% {background-position: 200px;}
                }
                .cleanlist-header {
                    font-size: clamp(2.5em, 8vw, 6em);
                    font-weight: 900;
                    background: linear-gradient(90deg, #ff8a65, #ffd54f);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: shine 3s infinite linear;
                    background-size: 400px;
                    margin-bottom: 30px;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }
                </style>
            
                <div style="text-align: center;">
                    <h1 class="cleanlist-header">🍑 CleanList</h1>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 🎨 Color palette for item-level styling
            item_colors = ["#e0f7fa", "#fce4ec", "#f3e5f5", "#e8f5e9", "#fff3e0", "#ede7f6", "#f9fbe7", "#e1f5fe"]

            for item_index, item_dict in enumerate(st.session_state.item_list):
                item_text = item_dict["label"]
                label = normalize_text(item_text)
                brand_list = grocery_brands_db.get(label) or grocery_brands_db.get(item_text)
                if not brand_list:
                    st.markdown(f"<div style='color:gray;font-style:italic;'>{item_text} → No brands found.</div>", unsafe_allow_html=True)
                    continue

                brand_scores = []
                for brand in brand_list:
                    ingredients = grocery_item_db.get(brand, ["Ingredients Not Available"])
                    score = score_item(brand, ingredients)[0]  # numeric score
                    brand_scores.append((brand, score, ingredients))

                # ✅ Sort by score (ascending = cleanest first)
                brand_scores.sort(key=lambda x: x[1], reverse=True)

                # ✅ Generate sleek numbers AFTER sorting
                sleek_numbers = generate_sleek_numbers(len(brand_scores))

                # 🎨 Assign consistent color per item
                item_color = "#ffffff" if i != 0 else item_colors[item_index % len(item_colors)]

                st.markdown(f"<h3 style='margin-top:40px;'>🧺 <u>{item_text}</u></h3>", unsafe_allow_html=True)

                # Get min and max scores for scaling
                scores_only = [s for _, s, _ in brand_scores]
                min_score = min(scores_only)
                max_score = max(scores_only)
                score_range = max_score - min_score or 1
                
                for i, (brand, score, ingredients) in enumerate(brand_scores):
                    number = sleek_numbers[i]
                    number_html = f"<span style='background-color:#333;color:#fff;padding:4px 10px;border-radius:20px;font-weight:bold;'>#{i + 1}</span>"
                    brand_line_html = (
                        f"<div style='display: flex; align-items: center; gap: 12px;'>"
                        f"{number_html}"
                        f"<span style='font-weight: bold;'>{brand}</span>"
                        f"</div>"
                        )
                    # Flip scaling so cleanest = biggest
                    raw_normalized = 1 - (score - min_score) / score_range
                    normalized = raw_normalized ** 0.5  # square root curve
                
                    # Boost top brand visually
                    if i == 0:
                        padding = 40
                        font_size = 1.6
                        shadow_strength = 0.25
                    else:
                        padding = 20 + int(normalized * 20)         # 20–40px
                        font_size = 1.0 + normalized * 0.4          # 1.0–1.4em
                        shadow_strength = 0.08 + normalized * 0.17  # 0.08–0.25
                
                    border_style = (
                        "4px solid #ff5722; box-shadow: 0 0 20px rgba(255, 87, 34, 0.6); background-image: linear-gradient(135deg, #ffe0b2, #ffccbc);"
                        if i == 0 else
                        "1px solid #ddd;"
                    )
                    
                    clean_score_html = f"<span style='background: linear-gradient(90deg, #4caf50, #81c784); color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 1em; display: inline-block;'>{score}</span>"
                    
                    item_formatted = color_code_ingredients(ingredients, score)
                    joined_items = (
                        item_formatted[1]
                        if item_formatted[1] == "Ingredients Not Available"
                        else ", ".join(item_formatted[1])
                    )
                
                    badge_html = "<div style='color:#fff;background-color:#ff5722;padding:8px 20px;border-radius:20px;display:inline-block;font-weight:bold;margin-bottom:10px;'>🏆 Top Pick</div>"
                    top_badge = badge_html if i == 0 else ""
                
                    html_block = (
                        f"<div style='background-color: {item_color}; border-radius: 12px; padding: {padding}px; "
                        f"margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,{shadow_strength}); border: {border_style}; transition: all 0.3s ease;'>"
                        f"{top_badge}"
                        f"<div style='font-size:{font_size}em; font-weight:bold; margin-bottom:10px;'>"
                        f"{number_html} {brand}"
                        f"</div>"
                        f"<div style='font-size:1em;'>"
                        f"<div><span style='font-weight:bold;'>→ CleanScore:</span> {clean_score_html}</div>"
                        f"<div><span style='font-weight:bold;'>| Ingredients:</span> {joined_items}</div>"
                        f"</div>"
                        f"</div>"
                    )
                    
                    st.markdown(html_block, unsafe_allow_html=True)
            st.session_state.show_create_cleanlist_button = False  # Optional: hide after click
        st.markdown('</div>', unsafe_allow_html=True)            
elif not st.session_state.editing and not st.session_state.item_list:
    if not st.session_state.just_interacted and st.session_state.app_initialized:
        flash_message("Your CleanList is currently empty.", msg_type="info", duration=2)

st.session_state.just_interacted = False         # Reset interaction flag for next rerun

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Image Upload ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*

