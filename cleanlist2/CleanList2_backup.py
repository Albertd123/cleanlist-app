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
    "alfalfa", "eggplant (BARI Bt Begun varieties)",
    "palm oil", "corn syrup", "high fructose corn syrup", "soybean oil", 
    "vegetable oil", "rapeseed oil", "soy protein isolate", "wheat flour", 
    "refined flour", "white flour", "enriched flour", "sugar", "glucose", 
    "fructose", "dextrose", "maltodextrin", "papaya", "summer squash", "potato", 
    "apple", "pink pineapple", "cottonseed oil"
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
    "palm oil", 
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

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Heuristic CleanScore engine ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*

# --- Predefined Grocery Database  ---
grocery_item_db = {
    "granola_Quaker Oats": ["organic oats", "cane sugar", "honey", "almonds"],
    "Justin's": ["roasted peanuts", "salt", "palm oil"],
    "Maruchan Instant Lunch": ["wheat flour", "salt", "monosodium glutamate", "vegetable oil"],
    "Almond Breeze": ["filtered water", "almonds", "calcium carbonate", "vitamin D2"],
    "Quest": ["soy protein isolate", "chocolate chips", "sugar", "natural flavors"]
}

grocery_brands_db = {
     "granola": ['granola_Quaker Oats'],
     "peanut butter": ["Justin's"],
     "instant noodles": ["Maruchan Instant Lunch"],
     "almond milk": ["Almond Breeze"],
     "protein bar": ["Quest"]
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
    if ingredient in GMO_INGREDIENTS or ARTIFICIAL_INGREDIENTS:
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
            if item_text in key: 
                top_brand_name = values[0]                          # Concatenate key with its first value 
                top_brand_name_clean = top_brand_name.strip()       # Clean up any extra spaces to match list1 keys
                for k in grocery_item_db:                           # Search for matching key in list1 (strip keys to avoid spacing issues) 
                    if k.strip() == top_brand_name_clean: 
                        return grocery_item_db[k] 
        else:
            return input_value

# ///////////////////////   ******** Function to compute a bounded CleanScore ******** 
def score_item(item: str, ingredients: Optional[str]) -> Tuple[int, Dict[str, List[str]]]:
    base = 50
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
    score += 14 * len(matched["GMO"])                  # per unique positive 
    score -= 7 * len(matched["AI"])              # per unique moderate negative 
    score -= 14 * len(matched["both"])               # per unique strong negative 
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

# ---------- Sidebar ----------
st.sidebar.markdown("""
    <div style="
        font-weight: bold;
        font-size: 50px;
        color: peach;
        text-shadow: -1px -1px 0 green, 1px -1px 0 black,
                     -1px 1px 0 green, 1px 1px 0 black;
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    ">
        Menu
    </div>
""", unsafe_allow_html=True)
with st.sidebar.expander("Groceries"):
    st.markdown("- Apples\n- Bananas\n- Bread")

with st.sidebar.expander("Favorites"):
    st.markdown("- Granola\n- Almond Milk")

with st.sidebar.expander("Suggestions"):
    st.markdown("- Try oat milk\n- Add leafy greens")

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


# ---------- Main Content ----------
#  Initialize empty list
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
    
#///////////////////////  ******** Get User Input ********
# ---------- Input field ----------
new_item = st.text_input("Add an item to your list", placeholder="e.g. Granola", key="add_item_input")

# ---------- Filtered suggestions (only when typing) ----------
typed = new_item.strip().lower()
matches = [brand for brand in grocery_brands_db if typed and typed in brand.lower()]

if matches:
    st.markdown("#### Choose from the following")
    for match in matches:
        match_lower = match.lower()
        match_index = match_lower.find(typed)
        highlighted = (
            f"{match[:match_index]}"
            f"<span style='background-color:#ffd700; font-weight:bold;'>"
            f"{match[match_index:match_index+len(typed)]}</span>"
            f"{match[match_index+len(typed):]}"
        )
        if st.button(match, key=f"suggestion_{match}"):
            st.session_state.prefill_input = match
            st.rerun()
        st.markdown(f"<div style='margin-top:-10px;'>{highlighted}</div>", unsafe_allow_html=True)

# ---------- Add to list ----------
if st.button("Add to list"):
    input_value = st.session_state.get("add_item_input", "").strip()
    normalized_input = input_value.lower()

    if not input_value:
        st.warning("Please enter an item before adding.")
    elif input_value not in grocery_brands_db:
        st.warning("Item not in database.")
    else:
        existing_labels = [it["label"].strip().lower() for it in st.session_state.item_list]
        if normalized_input in existing_labels:
            st.warning(f"'{input_value}' is already in your CleanList.")
        else:
            st.session_state.item_list.append({
                "id": f"it_{uuid4().hex}",
                "label": input_value
            })
            st.session_state.show_create_button = True
            st.success(f"Added: {input_value}")

# ---------- Conditionally show "Create My CleanList" button ----------
if st.session_state.show_create_button:
    st.button("Create My CleanList")


# ---------- Checkbox: "Select All" ----------
def _on_select_all_changed():
    val = st.session_state["select_all"]
    for it in st.session_state.item_list:
        st.session_state[f"sel_{it['id']}"] = val

# ---------- Editing UI (only when editing) ----------
if st.session_state.editing and st.session_state.item_list:
    st.checkbox("Select All", key="select_all", on_change=_on_select_all_changed)
    st.markdown("### 🧺 Select items to remove:")
    for i, it in enumerate(st.session_state.item_list, 1):
        st.checkbox(f"{i}. {it['label']}", key=f"sel_{it['id']}")
        
    # ---------- Button: "Remove Selected Items" ----------
    if st.button("🗑️ Remove Selected Items"):
        st.session_state.just_interacted = True
        selected_ids = [it["id"] for it in st.session_state.item_list if st.session_state.get(f"sel_{it['id']}", False)]
        if selected_ids:
            # Rebuild list (don’t mutate while iterating)
            st.session_state.item_list = [it for it in st.session_state.item_list if it["id"] not in selected_ids]
            # Clean up checkbox state for removed items
            for sid in selected_ids:
                st.session_state.pop(f"sel_{sid}", None)
            flash_message(f"Removed: {len(selected_ids)} item(s)", msg_type="success", duration=1)
            st.session_state.app_initialized = True
            st.rerun()  # 🔁 Force immediate UI update
        else:
            flash_message("No items selected for removal.", msg_type="warning", duration=1)
            
    # ---------- Button: "Done Editing" ----------
    if st.button("✅ Done Editing"):
        st.session_state.editing = False
        st.session_state.just_interacted = True
        st.session_state.app_initialized = True
        st.rerun()  # 🔁 Force immediate UI update
            
# ---------- Current Items  List (always visible) ----------
if st.session_state.item_list:
    st.markdown("🧪 Current Items:")
    for i, it in enumerate(st.session_state.item_list, 1):
        st.markdown(f"{i}. {it['label']}")
else:
    if not st.session_state.item_list and not st.session_state.editing and not st.session_state.just_interacted and st.session_state.app_initialized:
        flash_message("Your CleanList is currently empty.", msg_type="info", duration=1)

st.session_state.just_interacted = False         # Reset interaction flag for next rerun

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

col1, col2 = st.columns([1, 1])
   
# ---------- Button: "Create My CleanList" (explicit action) ----------
if not st.session_state.editing and st.session_state.get("show_create_button", False):
    with col1:
        st.markdown('<div class="button-container">', unsafe_allow_html=True)
        create_clicked = st.button("🚀 Create My CleanList!")
        if create_clicked:
            st.session_state.just_interacted = True
            if not st.session_state.item_list:
                flash_message("Your list is empty. Add items before creating your CleanList.", msg_type="warning", duration=1.2)
            else:
                ingredients_array = []
                labels = []
                combined = []
                for it in st.session_state.item_list:
                    item_text = it["label"]
                    label= normalize_text(item_text)
                    labels.append(label)
                    try:
                        mapped = create_CleanList(label)  # expects a string in, returns mapped value or None
                    except NameError:
                        no_item_present = "Item Not Available"
                        ingredients_array.append(no_item_present)
                    else:
                        if mapped == label:
                            no_item_present = "Item Not Available"
                            ingredients_array.append(no_item_present)
                        else:
                            ingredients_array.append(mapped)
                
                labels_flat = flatten(labels) if isinstance(labels, list) else [labels]
                st.success("Your CleanList is ready!")
                st.markdown("### 🍑 CleanList:")
    
                for label, ingredients in zip(labels_flat, ingredients_array):
                    if ingredients == "Item Not Available":
                        ingredients = "Igredients Not Available"
                        CleanScore = ["CleanScore Not Available"]
                    else:
                        CleanScore = score_item(label,ingredients)
                    item_formatted = color_code_ingredients(ingredients,CleanScore[0])
                    # if st.session_state.get("item_list"):
                    #     for i, item in enumerate(st.session_state.item_list, 1):
                    st.markdown(f"{label} **→** **CleanScore** = {item_formatted[0]}", unsafe_allow_html=True) 
                    if item_formatted[1] == "Igredients Not Available":
                        joined_items = ingredients
                    else:
                        joined_items = ", ".join(item_formatted[1])     # Join items into a single line, separated by commas
                    st.markdown(f"""<ul><li><span style='font-weight:bold;'>Ingredients →</span> {joined_items}</li></ul>""", unsafe_allow_html=True)
                    # st.markdown(f"&nbsp;&nbsp;&nbsp;- Ingredients **→** {joined_items}", unsafe_allow_html=True)  
        st.markdown('</div>', unsafe_allow_html=True)            

    # ---------- Button: Edit List (toggle) ----------
if not st.session_state.editing and st.session_state.item_list:
    with col2:
        if st.button("✏️ Edit List"):
            st.session_state.editing = True
            st.session_state.just_interacted = True
            st.session_state.app_initialized = True
            st.rerun()  # 🔁 Force immediate UI update
        st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
    
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Image Upload ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*

