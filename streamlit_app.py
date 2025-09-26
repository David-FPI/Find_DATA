import streamlit as st
import pandas as pd
import re

# -----------------
# Hàm chuẩn hóa
# -----------------
def normalize_phone(phone: str) -> str:
    if pd.isna(phone):
        return None
    phone = str(phone).strip()
    phone = re.sub(r"[^0-9]", "", phone)  # chỉ giữ số

    if phone.startswith("84") and len(phone) >= 9:
        phone = "0" + phone[2:]
    return phone

def normalize_email(email: str) -> str:
    if pd.isna(email):
        return None
    return str(email).strip().lower()

# -----------------
# Streamlit app
# -----------------
st.set_page_config(page_title="🔍 Find Tool", layout="wide")
st.title("📁 Find Tool trong Excel")

# Upload file
file = st.file_uploader("📤 Upload file Excel", type=["xlsx"])

if file:
    xls = pd.ExcelFile(file)

    # chọn skip row
    skip = st.number_input("⏭ Skip rows (số dòng bỏ qua)", 0, 20, 0)

    # chọn sheet
    sheets = st.multiselect("🧾 Chọn sheet để tìm", xls.sheet_names, default=xls.sheet_names[:1])

    if sheets:
        # đọc thử 1 sheet để lấy cột (dùng sheet đầu tiên trong danh sách)
        sample_df = pd.read_excel(file, sheet_name=sheets[0], skiprows=skip, dtype=str)

        # show sample data
        st.subheader("👀 Xem trước 5 dòng đầu của sheet")
        st.dataframe(sample_df.head(), use_container_width=True)

        # show data types
        st.write("🔍 Kiểu dữ liệu các cột:")
        st.json({col: str(dtype) for col, dtype in sample_df.dtypes.items()})

        # chọn cột
        col = st.selectbox("🎯 Chọn cột để dò", sample_df.columns)

        # option normalize
        norm_func = None
        if st.checkbox("✨ Chuẩn hóa dữ liệu (số ĐT / email)"):
            if "phone" in col.lower() or "sđt" in col.lower() or "điện thoại" in col.lower():
                norm_func = normalize_phone
                st.info("📱 Chuẩn hóa số điện thoại được bật")
            elif "email" in col.lower():
                norm_func = normalize_email
                st.info("📧 Chuẩn hóa email được bật")

        # nhập nhiều giá trị
        input_text = st.text_area("🔎 Nhập giá trị muốn tìm (mỗi dòng 1 SĐT/Email/Mã KH)")

        # nút bấm tìm
        if st.button("🚀 Tìm kiếm"):
            if not input_text.strip():
                st.warning("⚠️ Bạn chưa nhập giá trị tìm kiếm!")
            else:
                search_terms = [x.strip() for x in input_text.splitlines() if x.strip()]

                if norm_func:
                    search_terms = [norm_func(x) for x in search_terms]

                all_results = []

                for sheet in sheets:
                    df = pd.read_excel(file, sheet_name=sheet, skiprows=skip, dtype=str)
                    df_search = df.copy()

                    if norm_func:
                        df_search[col] = df_search[col].map(norm_func)

                    result = df[df_search[col].isin(search_terms)].copy()
                    if not result.empty:
                        result["Sheet Name"] = sheet
                        all_results.append(result)

                if all_results:
                    final_result = pd.concat(all_results, ignore_index=True)
                    st.success(f"✅ Tìm thấy {len(final_result)} dòng phù hợp")
                    st.dataframe(final_result, use_container_width=True)

                    # cho download kết quả
                    csv = final_result.to_csv(index=False)
                    st.download_button("📥 Tải kết quả CSV", csv, file_name="ket_qua_tim.csv", mime="text/csv")

                else:
                    st.warning("❌ Không tìm thấy giá trị nào trong file")
