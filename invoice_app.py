"""
invoice_app.py
Smart Invoice AI - Streamlit app.

Chalane ka tareeqa (smart-invoice folder mein):
    python -m streamlit run invoice_app.py
"""
import re
from datetime import date, datetime

import streamlit as st

import ledger
from extractor import extract_invoice

CURRENCIES = ["PKR", "USD", "EUR", "GBP", "AUD", "CAD", "AED", "SAR"]

CATEGORIES = [
    "Client Payment",
    "Platform Fees",
    "Software & Tools",
    "Equipment",
    "Internet & Utilities",
    "Marketing",
    "Office & Rent",
    "Travel",
    "Taxes",
    "Other",
]

# Simple keyword rules (baad mein apne keywords add kar sakte ho)
KEYWORDS = {
    "Platform Fees": ["upwork", "fiverr", "freelancer", "payoneer", "paypal", "commission"],
    "Software & Tools": ["adobe", "figma", "canva", "github", "chatgpt", "openai", "notion",
                         "hosting", "domain", "namecheap", "godaddy", "subscription"],
    "Equipment": ["daraz", "laptop", "mouse", "keyboard", "monitor", "headphones", "camera", "ssd"],
    "Internet & Utilities": ["ptcl", "stormfiber", "nayatel", "jazz", "zong", "telenor", "ufone",
                             "k-electric", "lesco", "iesco", "electricity", "internet", "wifi"],
    "Marketing": ["facebook ads", "google ads", "linkedin", "advertising"],
    "Office & Rent": ["rent", "coworking", "office"],
    "Travel": ["uber", "careem", "indrive", "fuel", "petrol"],
    "Taxes": ["fbr", "income tax"],
}


def suggest_category(vendor, items, tx_type):
    if tx_type == "income":
        return "Client Payment"
    text = f"{vendor or ''} {' '.join(items or [])}".lower()
    for category, words in KEYWORDS.items():
        for w in words:
            if re.search(r"\b" + re.escape(w) + r"\b", text):
                return category
    return "Other"


def detect_currency(extracted, raw_text, default):
    """Sirf tab currency maano jab text mein sach mein likhi ho, warna default."""
    code = str(extracted.get("currency") or "").upper().strip()
    upper = raw_text.upper()
    if code in CURRENCIES and re.search(r"\b" + code + r"\b", upper):
        return code
    if re.search(r"\bPKR\b|\bRS\b|\bRS\.|RUPEE", upper):
        return "PKR"
    return default


def to_float(value):
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def parse_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return date.today()


# ---------------------------------------------------------------- page setup
st.set_page_config(page_title="Smart Invoice AI", page_icon="🧾", layout="wide")
ledger.init_db()

st.title("🧾 Smart Invoice AI")
st.caption("Sab kuch aapke computer par process hota hai. Koi invoice cloud par nahi jata.")

default_currency = st.sidebar.selectbox("Default currency", CURRENCIES, index=0)

tab_add, tab_list, tab_report = st.tabs(["➕ Add invoice", "📋 Transactions", "📊 Monthly report"])

# ---------------------------------------------------------------- add invoice
with tab_add:
    upload = st.file_uploader("Invoice ya receipt ki image", type=["png", "jpg", "jpeg"])

    if upload is not None:
        file_id = f"{upload.name}-{upload.size}"

        # Har nayi file par sirf ek baar extraction chalao
        if st.session_state.get("file_id") != file_id:
            saved = ledger.UPLOAD_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{upload.name}"
            ledger.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(upload.getvalue())
            with st.spinner("Padh raha hoon... (pehli baar 30-60 second lag sakte hain)"):
                result = extract_invoice(str(saved))
            st.session_state["file_id"] = file_id
            st.session_state["result"] = result
            st.session_state["saved_path"] = str(saved)

        result = st.session_state["result"]
        raw_text = result.get("raw_text", "")

        if "error" in result:
            st.warning(f"Auto-extraction mein masla: {result['error']}. Neeche khud bhar do.")

        tx_type_guess = result.get("type") if result.get("type") in ("income", "expense") else "expense"
        vendor_guess = result.get("vendor") or ""
        items = result.get("items") or []
        if not isinstance(items, list):
            items = [str(items)]
        category_guess = suggest_category(vendor_guess, [str(i) for i in items], tx_type_guess)
        currency_guess = detect_currency(result, raw_text, default_currency)

        col_img, col_form = st.columns(2)
        with col_img:
            st.image(upload, caption=upload.name, width="stretch")
            with st.expander("OCR se nikla hua text"):
                st.text(raw_text or "(kuch nahi mila)")

        with col_form:
            st.subheader("Check karo aur theek karo")
            with st.form(f"form_{file_id}"):
                f_date = st.date_input("Date", value=parse_date(result.get("date")))
                f_vendor = st.text_input("Vendor / Client", value=vendor_guess)
                f_amount = st.number_input(
                    "Total amount", min_value=0.0, step=1.0, format="%.2f",
                    value=to_float(result.get("total")),
                )
                f_currency = st.selectbox(
                    "Currency", CURRENCIES, index=CURRENCIES.index(currency_guess)
                )
                f_type = st.selectbox(
                    "Type", ["expense", "income"], index=["expense", "income"].index(tx_type_guess)
                )
                f_category = st.selectbox(
                    "Category", CATEGORIES, index=CATEGORIES.index(category_guess)
                )
                f_notes = st.text_input("Notes (optional)")
                submitted = st.form_submit_button("💾 Save")

            if submitted:
                if f_amount <= 0:
                    st.error("Amount 0 se zyada hona chahiye.")
                else:
                    ledger.add_transaction({
                        "date": f_date.isoformat(),
                        "vendor": f_vendor,
                        "amount": f_amount,
                        "currency": f_currency,
                        "type": f_type,
                        "category": f_category,
                        "file_path": st.session_state["saved_path"],
                        "notes": f_notes,
                    })
                    st.success("Save ho gaya! 'Transactions' tab mein dekh lo.")

# ---------------------------------------------------------------- transactions
with tab_list:
    df = ledger.get_all()
    if df.empty:
        st.info("Abhi koi transaction nahi hai. Pehle 'Add invoice' tab se kuch save karo.")
    else:
        st.dataframe(df.drop(columns=["file_path"]), width="stretch", hide_index=True)
        st.subheader("Delete")
        del_id = st.number_input("Transaction id", min_value=1, step=1, key="del_id")
        if st.button("🗑️ Delete is id ko"):
            ledger.delete_transaction(del_id)
            st.rerun()

# ---------------------------------------------------------------- report
with tab_report:
    df = ledger.get_all()
    if df.empty:
        st.info("Report ke liye pehle kuch transactions save karo.")
    else:
        currency = st.selectbox("Currency", sorted(df["currency"].unique()), key="rep_cur")
        summary = ledger.monthly_summary(df, currency)

        total_income = summary["income"].sum()
        total_expense = summary["expense"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total income", f"{total_income:,.2f} {currency}")
        c2.metric("Total expenses", f"{total_expense:,.2f} {currency}")
        c3.metric("Profit", f"{total_income - total_expense:,.2f} {currency}")

        st.subheader("Month-wise")
        st.bar_chart(summary[["income", "expense"]])
        st.dataframe(summary.round(2), width="stretch")
        st.download_button(
            "⬇️ CSV download", summary.to_csv().encode("utf-8"),
            file_name=f"monthly_report_{currency}.csv", mime="text/csv",
        )

        st.subheader("Expenses by category")
        exp = df[(df["currency"] == currency) & (df["type"] == "expense")]
        if exp.empty:
            st.caption("Abhi koi expense nahi.")
        else:
            st.bar_chart(exp.groupby("category")["amount"].sum())
