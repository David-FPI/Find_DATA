import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🔍 Tìm kiếm SDT / Email", layout="wide")
st.title("📁 Tìm kiếm dữ liệu từ 1 file Excel nhiều sheet")

uploaded_file = st.file_uploader("📤 Tải lên 1 file Excel duy nhất", type=["xlsx", "xls"])

# Nếu chưa upload file, thì tự động lấy file mẫu từ GitHub
if not uploaded_file:
    st.info("📡 Chưa có file upload – đang lấy file mẫu từ GitHub...")

    default_url = "https://raw.githubusercontent.com/David-FPI/Find_DATA/main/Book1.xlsx"
    try:
        import requests
        response = requests.get(default_url)
        response.raise_for_status()
        uploaded_file = BytesIO(response.content)
        st.success("✅ Đã tải thành công file mẫu từ GitHub.")
    except Exception as e:
        st.error(f"❌ Không thể tải file mẫu từ GitHub: {e}")
        uploaded_file = None

skiprows_n = st.number_input("⏭ Số dòng đầu tiên muốn bỏ qua (skiprows)", min_value=0, max_value=20, value=0, step=1)

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
        sheet_names = xls.sheet_names

        # ✅ Cho phép chọn sheet
        selected_sheets = st.multiselect(
            "🧾 Chọn sheet để tìm kiếm:",
            options=sheet_names,
            default=sheet_names  # mặc định chọn hết
        )

        all_data = []
        for sheet_name in selected_sheets:
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=skiprows_n)
                df["Tên sheet"] = sheet_name
                all_data.append(df)
            except Exception as sheet_error:
                st.warning(f"⚠️ Bỏ qua sheet lỗi: `{sheet_name}` – {sheet_error}")

        if all_data:
            full_df = pd.concat(all_data, ignore_index=True)
            st.success(f"✅ Đã đọc {len(full_df)} dòng từ {len(selected_sheets)} sheet đã chọn.")

            # ✅ Chọn cột để tìm kiếm
            st.subheader("🧩 Chọn cột chứa giá trị cần tìm (SĐT / Email / Mã KH...)")
            possible_cols = full_df.columns.tolist()
            selected_col = st.selectbox("🎯 Chọn cột cần tra cứu:", options=possible_cols)

            st.subheader("🔎 Nhập danh sách SĐT hoặc Email để tìm (mỗi dòng 1 giá trị)")
            input_text = st.text_area("📥 Nhập dữ liệu:", placeholder="vd:\n0987654321\nuser@email.com")

            if st.button("🚀 Tìm kiếm"):
                if input_text.strip() == "":
                    st.warning("⚠️ Bạn chưa nhập gì cả!")
                else:
                    search_terms = [line.strip().lower() for line in input_text.splitlines() if line.strip()]
                    search_set = set(search_terms)

                    try:
                        target_col_series = full_df[selected_col].astype(str).str.strip().str.lower()
                    except Exception as e:
                        st.error(f"❌ Không thể lấy cột `{selected_col}`: {e}")
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

    except Exception as file_error:
        st.error(f"❌ Lỗi đọc file: {file_error}")
