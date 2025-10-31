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


# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                                                          ---- Heuristic CleanScore engine ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
STRONG_NEG = [  #sugars/syrups 
                "sugar", "high fructose corn syrup", "corn syrup",
    
                #trans & hydrogenated fats 
                "partially hydrogenated", "hydrogenated", "trans fat", "shortening", "bacon", "sausage"
    
                # preservatives/antioxidants 
                "bht", "bha", "tbhq", "propyl gallate","calcium carbonate",
    
                # msg & intense additives 
                "monosodium glutamate", "msg",
    
                # colors 
                "red 40", "yellow 5", "yellow 6", "blue 1", "blue 2", "caramel color", 
    
                # nitrites/nitrates 
                "sodium nitrite", "sodium nitrate", "nitrite", "nitrate",
    
                # emulsifiers/solvents with concern 
                "polysorbate 80", "propylene glycol", "titanium dioxide",
    
                # bromated flours 
                "potassium bromate", "bromated",
    
                # intense sweeteners 
                "aspartame", "sucralose", "acesulfame", "saccharin",
    
                # gums sometimes flagged 
                "carboxymethylcellulose", "carrageenan",
    
                # generic artificial 
                "artificial flavor", "artificial flavours", "artificial color", "artificial colour", ] 

MOD_NEG = [ # common added sugars / refined carbs 
            "cane sugar", "glucose", "dextrose", "fructose", "invert sugar", "maltodextrin", "enriched flour", "bleached flour", "white flour", 
            "refined flour", "wheat flour", "chocolate chips",
            
            # seed/veg oils (context dependent, treated as moderate) 
            "canola oil", "soybean oil", "vegetable oil", "palm oil", "corn oil", "rapeseed oil", 

            #Nuts
            "almonds", "roasted peanuts",
    
            # additives/preservatives 
            "salt", "sodium benzoate", "potassium sorbate", "disodium phosphate", "phosphate", "xanthan gum", "guar gum", "natural flavor", "natural flavors",
            "natural flavour", "natural flavours",
            
            #Powders
            "soy protein isolate"] 

POSITIVE = [ # quality signals / processing 
            "honey", "organic", "non-gmo", "no added sugar", "unsweetened", "unsalted", "low sodium", "sprouted", "fermented", "probiotic", 
    
            # proteins/fats 
            "grass-fed", "pasture-raised", "wild-caught", "extra virgin olive oil", "olive oil", "avocado oil", 
    
            # grains/legumes 
            "whole grain", "100% whole", "whole wheat", "steel-cut oats", "brown rice", "quinoa", "lentils", "beans", "chickpeas", "high fiber", 
    
            # produce & dairy descriptors 
            "spinach", "kale", "broccoli", "berries", "plain yogurt", "greek yogurt", "whole milk yogurt",
    
            # cured meat improvements 
            "no nitrate", "no nitrite", "nitrite-free", "nitrate-free" 

            #Seasoning
            "onion", "garlic", "pepper",
    
            #Liquids
            "filtered water"
    
            #Vitamins
            "vitamin D2" ] 

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
    if ingredient in MOD_NEG:
        return f"<span style='color:orange'>{ingredient}</strong></span>"
    elif ingredient in STRONG_NEG:
        return f"<span style='color:red'>{ingredient}</strong></span>"
#   elif ingredient in POSITIVE:
#       return f"<span style='color:green'>{ingredient}</strong></span>"
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
    matched = {"positive": [], "moderate_neg": [], "strong_neg": []}
    
    # Positive signals 
    for kw in POSITIVE: 
        if kw in ing_text: 
            matched["positive"].append(kw) 
            
    # Negative signals (moderate) 
    for kw in MOD_NEG: 
        if kw in ing_text: 
            matched["moderate_neg"].append(kw) 
     
    # Strong negatives 
    for kw in STRONG_NEG: 
        if kw in ing_text: 
            matched["strong_neg"].append(kw)    

    # Scoring logic (bounded) 
    score = base 
    score += 14 * len(matched["positive"])                  # per unique positive 
    score -= 7 * len(matched["moderate_neg"])              # per unique moderate negative 
    score -= 14 * len(matched["strong_neg"])               # per unique strong negative 
    # score += 5 * min(2, len(matched["whole_food"]))        # small boosts for whole-food hints 
    # score -= 10 * min(2, len(matched["ultra_processed"]))  # small penalties for ultra-processed hints
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
    
        # Display CleanScore with colored text
        # st.markdown(f"<h3 style='color:{color}'>CleanScore = {final_score[0]}/100</h3>", unsafe_allow_html=True)       
    else:
        st.error("Item not found.")
    return final_score  

#///////////////////////   ******** Function for Defensive Flattening ********
def flatten(lst):
    return [item for sublist in lst for item in (sublist if isinstance(sublist, list) else [sublist])]
    
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*
#                          🛒 📝 🧪 🧺  🛒 📝 🧪 🧺 ---- Streamlit UI ---- ✅ 📋 🧼 🍑 🔐
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
        font-size: 60px;
        color: peach;
        text-shadow: -1px -1px 0 green, 1px -1px 0 black,
                     -1px 1px 0 green, 1px 1px 0 black;
        text-align: center;
        display: block;
        margin-bottom: 0.5rem;
    ">
        🍑 Menu
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
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #eee;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

with open("CleanList logo.png", "rb") as f:
    logo_data = base64.b64encode(f.read()).decode() 
st.markdown(f"""
    <div style="display: flex; justify-content: center; margin-top: 2rem; margin-bottom: 0.5rem;">
        <a href="http://192.168.1.77:8501" target="_blank">
            <img src="data:image/png;base64,{logo_data}" style="max-width: 250px; height: auto;" class="responsive-logo">
        </a>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 4, 1])
# with col1:

# ---------- Sticky Header ----------
st.markdown("""
    <div class="sticky-header">
        <h1 style="margin: 0;">Level-Up your grocery list with clarity and ease!</h1>
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
    
#///////////////////////  ******** Get User Input ********

# ---------- Textbox: Add Items ----------
with st.form(key="add_unique_item_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])  # Wider input, narrower button
    with col1:
        new_item = st.text_input("Add an item to your list", placeholder="e.g. Granola", key="add_item_input")
        submitted = st.form_submit_button("Add to list")
    
# ---------- Save User Input ----------
if submitted:
    st.session_state.just_interacted = True
    st.session_state.app_initialized = True
    if new_item:
        normalized_input = new_item.strip().lower()
        existing_labels = [it["label"].strip().lower() for it in st.session_state.item_list]
        if normalized_input in existing_labels:
            flash_message(f"'{new_item}' is already in your CleanList.", msg_type="warning", duration=2)
        else:
            st.session_state.item_list.append({
                "id": f"it_{uuid4().hex}",
                "label": new_item.strip()
            })
            flash_message(f"Added: {new_item}", msg_type="success", duration=1)
    else:
        flash_message("Please enter an item before adding.", msg_type="warning", duration=1)

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
    st.markdown("📝 Current Items:")
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
                st.markdown(f"- {label} **→** **CleanScore** = {CleanScore[0]}, Ingredients **→** {ingredients}")
                # st.markdown(f"- **Ingredients**: {ingredients}")
                # st.markdown(f"🧪 **CleanScore**: {CleanScore[0]}")
                
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
#                                                          ---- Inamge Upload ----
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-**-*-*-*-*-*-*-*-*-*--*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-**-*-*-*-*


#/////////////////////// ******** Scraper function ********
# def scrape_publix_item(item):
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1920x1080")
#     driver = webdriver.Chrome(options=options)

#     try:
#         # Step 1: Search Publix
#         search_url = f"https://www.publix.com/search?q={item}"
#         driver.get(search_url)
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-card")))

#         # Step 2: Click first product
#         first_product = driver.find_element(By.CLASS_NAME, "product-card")
#         product_link = first_product.find_element(By.TAG_NAME, "a").get_attribute("href")
#         driver.get(product_link)
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-details")))

#         # Step 3: Extract content using BeautifulSoup
#         soup = BeautifulSoup(driver.page_source, "html.parser")

#         # Product name
#         #name_tag = soup.find("h1")
#         name = driver.find_element(By.CLASS_NAME, "product-title").text #name = name_tag.text.strip() if name_tag else "Name not found"

#         # Price
#         price_tag = soup.find("span", class_="product-price")
#         price = price_tag.text.strip() if price_tag else "Price not found"

#         # Ingredients
#         ingredients_section = soup.find("div", class_="product-ingredients")
#         ingredients = ingredients_section.text.strip() if ingredients_section else "Ingredients not found"

#         return {
#             "name": name,
#             "price": price,
#             "ingredients": ingredients
#         }

#     except Exception as e:
#         return None
#     finally:
#         driver.quit()