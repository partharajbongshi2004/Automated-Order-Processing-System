# 👕 Automated Clothing Order Processing System

An intelligent, end-to-end order management dashboard built with **Streamlit**, **SQLite**, and the **Google GenAI SDK (`gemini-2.5-flash`)**. 

This application converts unstructured customer messages (from emails, DMs, or chat) into structured JSON order data, validates real-time warehouse inventory, atomically updates stock levels, and generates downloadable customer invoices.

---

## ✨ Key Features

* **🤖 AI-Powered Order Extraction:** Uses **Gemini 2.5 Flash** with Pydantic structured outputs (`response_schema`) to accurately map casual customer messages to exact store catalog items, sizes, and quantities.
* **🛡️ Zero-Downtime Fallback Engine:** Automatically switches to a built-in regex and keyword-matching rule engine when no API key is provided or if the API is unreachable.
* **🗄️ Atomic SQLite Inventory Management:** Pre-seeded product catalog with transactional stock validation and thread-safe stock deduction to prevent overselling.
* **🧾 Instant Invoice Generation:** Automatically calculates line-item totals, assigns unique invoice numbers (`INV-YYYYMMDD-HHMMSS`), and lets staff download `.txt` receipts in one click.
* **📊 Real-Time Streamlit Dashboard:** Live inventory tracking, low-stock alerts, one-click sample messages for quick testing, and a complete audit log of processed orders.

---

## 🏗️ Project Architecture

```text
clothing_order_system/
├── app.py               # Streamlit web dashboard, UI state, & invoice generator
├── ai_processor.py      # Google GenAI SDK integration & rule-based fallback parser
├── database.py          # SQLite schema initialization, stock validation, & order logging
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

### How It Works
1. **Input:** A store operator pastes a raw customer message (e.g., *"Hey! Can I grab two large oversized fleece hoodies?"*).
2. **Extraction:** `ai_processor.py` sends the message and current product catalog to **Gemini 2.5 Flash** (or the local fallback engine) to return strict JSON:
   ```json
   {
     "product_name": "Oversized Fleece Hoodie",
     "size": "L",
     "quantity": 2
   }
   ```
3. **Validation & Fulfillment:** `database.py` checks if the SKU exists and has sufficient stock. If valid, it deducts the stock and logs the order inside a single database transaction.
4. **Invoicing:** `app.py` renders an itemized receipt and updates the live inventory and order history tables.

---

## 🚀 Getting Started

### Prerequisites
* **Python 3.9+** installed on your machine.
* *(Optional)* A **Google Gemini API Key** from [Google AI Studio](https://google.com).

### Installation

1. **Clone or create the project directory:**
   ```bash
   mkdir clothing_order_system
   cd clothing_order_system
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate        # On macOS/Linux
   venv\Scripts\activate           # On Windows
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. **(Optional) Set your Gemini API key as an environment variable:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"   # macOS/Linux
   set GEMINI_API_KEY="your_api_key_here"      # Windows CMD
   ```
   > **Note:** You can also enter your API key directly in the app's sidebar at runtime, or leave it blank to run in **Fallback Mode**.

2. **Launch the Streamlit dashboard:**
   ```bash
   streamlit run app.py
   ```

3. Open your browser to `http://localhost:8501`.

---

## 📦 Pre-Seeded Store Catalog

On first launch, `database.py` automatically creates `clothing_store.db` and populates it with the following inventory:

| Product Name | Available Sizes | Unit Price |
| :--- | :--- | :---: |
| **Classic Cotton T-Shirt** | S, M, L, XL | $25.00 |
| **Slim Fit Denim Jeans** | S, M, L, XL | $60.00 |
| **Oversized Fleece Hoodie** | S, M, L, XL | $55.00 |
| **Linen Summer Shirt** | S, M, L | $45.00 |
| **Lightweight Windbreaker Jacket** | M, L, XL | $85.00 |

---

## 🧪 Testing the System

Use the **Sample Customer Messages** in the left sidebar or try your own natural language inputs:
* *"Hi! Can I order two Large Oversized Fleece Hoodies please?"*
* *"I'd like to buy 3 Classic Cotton T-Shirts in size Medium."*
* *"Send me 1 Slim Fit Denim Jeans, size XL."*
* *"Do you have 50 Lightweight Windbreaker Jackets in L?"* *(Tests automatic out-of-stock rejection)*

---

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io)
* **AI / NLP:** [Google GenAI SDK](https://pypi.org) (`gemini-2.5-flash`) & [Pydantic](https://pydantic.dev)
* **Database:** SQLite3 (`sqlite3` standard library)
* **Data Handling:** [Pandas](https://pydata.org)

---

## 📄 License

This project is open-source and available under the [MIT License](https://opensource.org).
