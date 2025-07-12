import streamlit as st
import pandas as pd

st.set_page_config(page_title="🔍 Tìm kiếm SDT / Email", layout="wide")
st.title("📁 Tìm kiếm dữ liệu từ 1 file Excel nhiều sheet")

uploaded_file = st.file_uploader("📤 Tải lên 1 file Excel duy nhất", type=["xlsx", "xls"])
skiprows_n = st.number_input("⏭ Số dòng đầu tiên muốn bỏ qua (skiprows)", min_value=0, max_value=20, value=1, step=1)

# Bước 1: Đọc dữ liệu nếu chưa đọc
if uploaded_file and "full_df" not in st.session_state:
    all_data = []
    loaded_sheets = []

    try:
        xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
        for sheet_name in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=skiprows_n)
                df["Tên sheet"] = sheet_name
                all_data.append(df)
                loaded_sheets.append(sheet_name)
            except Exception as sheet_error:
                st.warning(f"⚠️ Bỏ qua sheet lỗi: `{sheet_name}` – {sheet_error}")
    except Exception as file_error:
        st.error(f"❌ Lỗi đọc file: {file_error}")
        st.stop()

    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        st.session_state["full_df"] = full_df
        st.session_state["loaded_sheets"] = loaded_sheets
        st.success(f"✅ Đã đọc {len(full_df)} dòng từ {len(loaded_sheets)} sheet.")
    else:
        st.error("❌ Không có sheet nào đọc thành công.")
        st.stop()

# Bước 2: Cho chọn cột nếu đã có dữ liệu
if "full_df" in st.session_state:
    full_df = st.session_state["full_df"]
    loaded_sheets = st.session_state["loaded_sheets"]
    
    st.dataframe(pd.DataFrame(loaded_sheets, columns=["Tên sheet"]), use_container_width=True)

    st.subheader("🎯 Chọn cột chứa giá trị cần tìm (SĐT / Email / Mã KH...)")
    selected_col = st.selectbox("🧩 Cột cần tra cứu:", options=full_df.columns.tolist())

    input_text = st.text_area("📥 Nhập danh sách cần tìm (SĐT, Email...)", placeholder="0987xxx\nabc@gmail.com")

    if st.button("🚀 Bắt đầu tìm kiếm"):
        if not input_text.strip():
            st.warning("⚠️ Bạn chưa nhập gì để tìm!")
            st.stop()

        search_terms = [line.strip().lower() for line in input_text.splitlines() if line.strip()]
        search_set = set(search_terms)

        try:
            target_col_series = full_df[selected_col].astype(str).str.strip().str.lower()
        except Exception as e:
            st.error(f"❌ Không thể xử lý cột `{selected_col}`: {e}")
            st.stop()

        value_found = {}
        for val in search_set:
            matches = target_col_series[target_col_series == val]
            if not matches.empty:
                value_found[val] = matches.index.tolist()

        result_rows = []
        for val in search_terms:
            if val in value_found:
                last_row = full_df.loc[value_found[val][-1]].copy()
                last_row["Giá trị tìm"] = val
                result_rows.append(last_row)
            else:
                empty_row = pd.Series([None]*len(full_df.columns), index=full_df.columns)
                empty_row["Giá trị tìm"] = val
                result_rows.append(empty_row)

        result_df = pd.DataFrame(result_rows)
        result_df = result_df[["Giá trị tìm"] + [col for col in result_df.columns if col != "Giá trị tìm"]]

        st.subheader(f"📊 Tìm thấy {result_df[result_df.notna().any(axis=1)].shape[0]} / {len(search_terms)} giá trị")
        st.dataframe(result_df, use_container_width=True)

        csv = result_df.to_csv(index=False)
        st.download_button("📥 Tải kết quả CSV", csv, file_name="ket_qua_tim.csv", mime="text/csv")
