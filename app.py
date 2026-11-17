import pandas as pd
import streamlit as st
from ai_processor import extract_order_details
from database import (
    check_stock,
    get_all_orders,
    get_all_products,
    get_unique_product_names,
    init_db,
    process_and_save_order,
)

# Page configuration
st.set_page_config(
    page_title="AI Clothing Order Processor",
    page_icon="👕",
    layout="wide",
)

# Initialize SQLite database on app startup
init_db()


def format_invoice_text(invoice: dict) -> str:
    """Generate a clean text receipt for display and download."""
    return f"""========================================
        URBAN THREADS APPAREL
           OFFICIAL INVOICE
========================================
Invoice No : {invoice['order_number']}
Date       : {invoice['created_at']}
----------------------------------------
Item       : {invoice['product_name']}
Size       : {invoice['size']}
Quantity   : {invoice['quantity']}
Unit Price : ${invoice['unit_price']:.2f}
----------------------------------------
TOTAL PAID : ${invoice['total_price']:.2f}
========================================
Original Customer Note:
"{invoice['customer_message']}"
========================================
Thank you for shopping with us!
"""


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        placeholder="AIzaSy...",
        help="Leave blank to test using the built-in rule-based fallback extractor.",
    )
    if api_key_input:
        st.success("Gemini API Key active")
    else:
        st.info("Running in Fallback Mode (No API Key)")

    st.divider()
    st.subheader("💡 Sample Customer Messages")
    sample_messages = [
        "Hi! Can I order two Large Oversized Fleece Hoodies please?",
        "I'd like to buy 3 Classic Cotton T-Shirts in size Medium.",
        "Send me 1 Slim Fit Denim Jeans, size XL.",
        "Do you have 4 Lightweight Windbreaker Jackets in L?",
    ]
    for idx, sample in enumerate(sample_messages):
        if st.button(f"Use Sample #{idx + 1}", key=f"sample_{idx}", use_container_width=True):
            st.session_state["order_input"] = sample


# --- MAIN DASHBOARD ---
st.title("👕 Automated Clothing Order Processing System")
st.markdown(
    "Enter a raw customer order message below. The system uses **Google Gemini** to extract structured "
    "order details, validates **SQLite inventory**, updates stock automatically, and generates an **invoice**."
)

col_left, col_right = st.columns([1.15, 1], gap="large")

with col_left:
    st.subheader("📩 New Customer Order")

    default_text = st.session_state.get(
        "order_input", "Hey there! Could I get 2 Classic Cotton T-Shirts in size L?"
    )
    customer_message = st.text_area(
        "Customer Order Message",
        value=default_text,
        height=120,
        placeholder="e.g., I want to order 2 medium linen summer shirts...",
    )

    process_btn = st.button("🚀 Process Order & Generate Invoice", type="primary", use_container_width=True)

    if process_btn:
        if not customer_message.strip():
            st.warning("Please enter a customer order message first.")
        else:
            with st.spinner("Extracting order details and checking stock..."):
                catalog_names = get_unique_product_names()
                extracted = extract_order_details(
                    message=customer_message,
                    available_products=catalog_names,
                    api_key=api_key_input,
                )

                st.markdown("#### 🔍 Extracted Order Data")
                st.caption(f"Extraction Engine: **{extracted['extraction_method']}**")
                st.json(
                    {
                        "product_name": extracted["product_name"],
                        "size": extracted["size"],
                        "quantity": extracted["quantity"],
                    }
                )

                # Validate inventory
                is_available, status_msg, product_record = check_stock(
                    product_name=extracted["product_name"],
                    size=extracted["size"],
                    quantity=extracted["quantity"],
                )

                if not is_available:
                    st.error(f"❌ Order Rejected: {status_msg}")
                else:
                    # Update stock & save order
                    invoice_data = process_and_save_order(
                        customer_message=customer_message.strip(),
                        product_id=product_record["id"],
                        product_name=product_record["name"],
                        size=product_record["size"],
                        quantity=extracted["quantity"],
                        unit_price=product_record["price"],
                    )
                    st.success(f"✅ Order Confirmed! Stock automatically reduced by {extracted['quantity']}.")

                    # Display Generated Invoice
                    st.markdown("#### 🧾 Generated Invoice")
                    invoice_text = format_invoice_text(invoice_data)
                    st.code(invoice_text, language="text")

                    st.download_button(
                        label="⬇️ Download Invoice (.txt)",
                        data=invoice_text,
                        file_name=f"{invoice_data['order_number']}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

with col_right:
    st.subheader("📦 Live Store Inventory")
    products = get_all_products()
    df_products = pd.DataFrame(products)

    # Top summary metrics
    total_units = int(df_products["stock"].sum())
    low_stock_count = int((df_products["stock"] <= 5).sum())

    m1, m2 = st.columns(2)
    m1.metric("Total Units in Stock", total_units)
    m2.metric("Low Stock SKUs (≤5)", low_stock_count)

    # Display clean inventory table
    df_display = df_products[["name", "size", "price", "stock"]].copy()
    df_display.columns = ["Product Name", "Size", "Price ($)", "Available Stock"]
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=360,
    )

# --- RECENT ORDERS HISTORY ---
st.divider()
st.subheader("📜 Completed Orders History")
orders = get_all_orders()
if orders:
    df_orders = pd.DataFrame(orders)[
        ["order_number", "created_at", "product_name", "size", "quantity", "unit_price", "total_price"]
    ]
    df_orders.columns = [
        "Invoice #",
        "Timestamp",
        "Product",
        "Size",
        "Qty",
        "Unit Price ($)",
        "Total ($)",
    ]
    st.dataframe(df_orders, use_container_width=True, hide_index=True)
else:
    st.info("No orders have been processed yet.")
