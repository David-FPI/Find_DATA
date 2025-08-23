# genspark.py
import streamlit as st
import pandas as pd
import re

def extract_digits(phone):
    if pd.isna(phone):
        return None
    digits = re.sub(r'[^\d]', '', str(phone))  # Xóa mọi ký tự không phải số
    return digits[-8:] if len(digits) >= 8 else None  # Lấy đúng 9 số cuối

st.set_page_config(page_title="🔍 Tìm kiếm SDT / Email", layout="wide")
st.title("📁 Tìm kiếm dữ liệu từ 1 file Excel nhiều sheet")

uploaded_file = st.file_uploader("📤 Tải lên 1 file Excel duy nhất", type=["xlsx", "xls"])
# Nếu chưa upload file, thì tự động lấy file mẫu từ GitHub
if not uploaded_file:
    st.info("📡 Chưa có file upload – đang lấy file mẫu từ GitHub...")

    default_url = "https://raw.githubusercontent.com/David-FPI/Find_DATA/main/Book1.xlsx"
    try:
        import requests
        from io import BytesIO
        response = requests.get(default_url)
        response.raise_for_status()
        uploaded_file = BytesIO(response.content)
        st.success("✅ Đã tải thành công file mẫu từ GitHub.")
    except Exception as e:
        st.error(f"❌ Không thể tải file mẫu từ GitHub: {e}")
        uploaded_file = None

# Cho phép nhập số dòng cần bỏ qua
skiprows_n = st.number_input("⏭ Số dòng đầu tiên muốn bỏ qua (skiprows)", min_value=0, max_value=20, value=0, step=1)

if uploaded_file:
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

    # Hiển thị sheet đã đọc thành công
    if loaded_sheets:
        st.markdown("### ✅ Sheet đã đọc thành công:")
        selected_sheets = st.multiselect(
            "📑 Chọn sheet muốn sử dụng:",
            options=loaded_sheets,
            default=loaded_sheets  # mặc định chọn tất cả
        )
    
        st.dataframe(pd.DataFrame(selected_sheets, columns=["Sheet được chọn"]), use_container_width=True)
    
        # Lọc lại data chỉ lấy sheet user chọn
        # all_data = [df for df in all_data if df["Tên sheet"].iloc[0] in selected_sheets]
        all_data = [df for df in all_data if df["Tên sheet"].unique()[0] in selected_sheets]



    # Xử lý tìm kiếm nếu đọc xong dữ liệu
    if all_data:
        full_df = pd.concat(all_data, ignore_index=True)
        st.success(f"✅ Đã đọc tổng cộng {len(full_df)} dòng từ {len(loaded_sheets)} sheet.")

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
                # Tách input, chuẩn hóa về 9 số cuối
                search_terms = [line.strip() for line in input_text.splitlines() if line.strip()]
                search_core = [(raw, extract_digits(raw)) for raw in search_terms]
                search_set = set(core for _, core in search_core if core)

                try:
                    # Chuẩn hóa toàn bộ cột cần dò về 9 số cuối
                    target_core_series = full_df[selected_col].astype(str).apply(extract_digits)
                except Exception as e:
                    st.error(f"❌ Không thể xử lý số trong cột `{selected_col}`: {e}")
                    st.stop()

                # Dò match theo 9 số cuối
                value_found = {}
                for core in search_set:
                    matches = target_core_series[target_core_series == core]
                    if not matches.empty:
                        value_found[core] = matches.index.tolist()

                # Gộp kết quả lại theo từng input
                result_rows = []
                for raw_val, core_val in search_core:
                    if core_val in value_found:
                        last_idx = value_found[core_val][-1]
                        last_row = full_df.loc[last_idx].copy()
                        last_row["Giá trị tìm"] = raw_val
                        last_row["9 số cuối"] = core_val
                        result_rows.append(last_row)
                    else:
                        empty_row = pd.Series([None]*len(full_df.columns), index=full_df.columns)
                        empty_row["Giá trị tìm"] = raw_val
                        empty_row["9 số cuối"] = core_val
                        result_rows.append(empty_row)

                # Tạo DataFrame kết quả
                result_df = pd.DataFrame(result_rows)
                fixed_cols = ["Giá trị tìm", "9 số cuối"]
                other_cols = [col for col in result_df.columns if col not in fixed_cols]
                result_df = result_df[fixed_cols + other_cols]

                st.subheader(f"📊 Tìm thấy {result_df[result_df.notna().any(axis=1)].shape[0]} / {len(search_core)} giá trị")
                st.dataframe(result_df, use_container_width=True)

                # Xuất CSV
                csv = result_df.to_csv(index=False)
                st.download_button("📥 Tải kết quả CSV", csv, file_name="ket_qua_tim.csv", mime="text/csv")



# # genspark.py
# import streamlit as st
# import pandas as pd

# st.set_page_config(page_title="🔍 Tìm kiếm SDT / Email", layout="wide")
# st.title("📁 Tìm kiếm dữ liệu từ 1 file Excel nhiều sheet")

# uploaded_file = st.file_uploader("📤 Tải lên 1 file Excel duy nhất", type=["xlsx", "xls"])
# # Nếu chưa upload file, thì tự động lấy file mẫu từ GitHub
# if not uploaded_file:
#     st.info("📡 Chưa có file upload – đang lấy file mẫu từ GitHub...")

#     default_url = "https://raw.githubusercontent.com/David-FPI/Find_DATA/main/Book1.xlsx"
#     try:
#         import requests
#         from io import BytesIO
#         response = requests.get(default_url)
#         response.raise_for_status()
#         uploaded_file = BytesIO(response.content)
#         st.success("✅ Đã tải thành công file mẫu từ GitHub.")
#     except Exception as e:
#         st.error(f"❌ Không thể tải file mẫu từ GitHub: {e}")
#         uploaded_file = None

# # Cho phép nhập số dòng cần bỏ qua
# skiprows_n = st.number_input("⏭ Số dòng đầu tiên muốn bỏ qua (skiprows)", min_value=0, max_value=20, value=0, step=1)

# if uploaded_file:
#     all_data = []
#     loaded_sheets = []

#     try:
#         xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
#         for sheet_name in xls.sheet_names:
#             try:
#                 df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=skiprows_n)
#                 df["Tên sheet"] = sheet_name
#                 all_data.append(df)
#                 loaded_sheets.append(sheet_name)
#             except Exception as sheet_error:
#                 st.warning(f"⚠️ Bỏ qua sheet lỗi: `{sheet_name}` – {sheet_error}")
#     except Exception as file_error:
#         st.error(f"❌ Lỗi đọc file: {file_error}")

#     # Hiển thị sheet đã đọc thành công
#     if loaded_sheets:
#         st.markdown("### ✅ Sheet đã đọc thành công:")
#         st.dataframe(pd.DataFrame(loaded_sheets, columns=["Tên sheet"]), use_container_width=True)

#     # Xử lý tìm kiếm nếu đọc xong dữ liệu
#     if all_data:
#         full_df = pd.concat(all_data, ignore_index=True)
#         st.success(f"✅ Đã đọc tổng cộng {len(full_df)} dòng từ {len(loaded_sheets)} sheet.")

#         # ✅ Chọn cột để tìm kiếm
#         st.subheader("🧩 Chọn cột chứa giá trị cần tìm (SĐT / Email / Mã KH...)")
#         possible_cols = full_df.columns.tolist()
#         selected_col = st.selectbox("🎯 Chọn cột cần tra cứu:", options=possible_cols)

#         st.subheader("🔎 Nhập danh sách SĐT hoặc Email để tìm (mỗi dòng 1 giá trị)")
#         input_text = st.text_area("📥 Nhập dữ liệu:", placeholder="vd:\n0987654321\nuser@email.com")

#         if st.button("🚀 Tìm kiếm"):
#             if input_text.strip() == "":
#                 st.warning("⚠️ Bạn chưa nhập gì cả!")
#             else:
#                 search_terms = [line.strip().lower() for line in input_text.splitlines() if line.strip()]
#                 search_set = set(search_terms)

#                 # 👉 Dòng cần kiểm tra
#                 try:
#                     target_col_series = full_df[selected_col].astype(str).str.strip().str.lower()
#                 except Exception as e:
#                     st.error(f"❌ Không thể lấy cột `{selected_col}`: {e}")
#                     st.stop()

#                 value_found = {}
#                 for val in search_set:
#                     matches = target_col_series[target_col_series == val]
#                     if not matches.empty:
#                         value_found[val] = matches.index.tolist()

#                 result_rows = []
#                 for val in search_terms:
#                     if val in value_found:
#                         last_row = full_df.loc[value_found[val][-1]].copy()
#                         last_row["Giá trị tìm"] = val
#                         result_rows.append(last_row)
#                     else:
#                         empty_row = pd.Series([None]*len(full_df.columns), index=full_df.columns)
#                         empty_row["Giá trị tìm"] = val
#                         result_rows.append(empty_row)

#                 result_df = pd.DataFrame(result_rows)
#                 result_df = result_df[["Giá trị tìm"] + [col for col in result_df.columns if col != "Giá trị tìm"]]

#                 st.subheader(f"📊 Tìm thấy {result_df[result_df.notna().any(axis=1)].shape[0]} / {len(search_terms)} giá trị")
#                 st.dataframe(result_df, use_container_width=True)

#                 csv = result_df.to_csv(index=False)
#                 st.download_button("📥 Tải kết quả CSV", csv, file_name="ket_qua_tim.csv", mime="text/csv")
