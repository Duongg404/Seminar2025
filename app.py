import streamlit as st
import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sentiment_analyzer import SentimentAnalyzer
from preprocessor import VietnamesePreprocessor
from database import SentimentDatabase

# CẤU HÌNH TRANG STREAMLIT
st.set_page_config(
    page_title="Trợ lý phân loại cảm xúc Tiếng Việt",
    page_icon="😊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# KHỞI TẠO CÁC THÀNH PHẦN
@st.cache_resource
def load_analyzer():
    return SentimentAnalyzer()

@st.cache_resource
def load_preprocessor():
    return VietnamesePreprocessor()

@st.cache_resource
def load_database():
    return SentimentDatabase()

try:
    analyzer = load_analyzer()
    preprocessor = load_preprocessor()
    db = load_database()
except Exception as e:
    st.error(f"❌ Lỗi khởi tạo hệ thống: {str(e)}")
    st.stop()

# GIAO DIỆN CHÍNH
st.title("😊 Trợ lý phân loại cảm xúc Tiếng Việt")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Nhập câu tiếng Việt cần phân tích")

    user_input = st.text_area(
        "Nhập câu tại đây:",
        height=120,
        placeholder="Ví dụ: Hôm nay tôi rất vui, hoặc: Rat vui hom nay...",
        key="input_text"
    )

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        analyze_btn = st.button("🔍 Phân Loại Cảm Xúc", type="primary", width='stretch')

    with col_btn2:
        if st.button("🔄 Xóa nội dung", width='stretch'):
            st.rerun()

    st.markdown("---")

    st.subheader("📊 Kết Quả Phân Loại")

    if analyze_btn and user_input:
        with st.spinner("⏳ Đang phân tích cảm xúc..."):
            try:
                cleaned_text = preprocessor.normalize(user_input)

                if not cleaned_text or len(cleaned_text.strip()) < 3:
                    st.warning("⚠️ Câu nhập vào quá ngắn hoặc không hợp lệ!")
                else:
                    sentiment_label, confidence_score = analyzer.analyze(cleaned_text, confidence_threshold=0.3)

                    sentiment_display = {
                        "POSITIVE": {"text": "TÍCH CỰC 😊", "color": "green"},
                        "NEUTRAL": {"text": "TRUNG TÍNH 😐", "color": "gray"},
                        "NEGATIVE": {"text": "TIÊU CỰC 😞", "color": "red"}
                    }.get(sentiment_label, {"text": sentiment_label, "color": "blue"})

                    db.save_record(
                        original_text=user_input,
                        cleaned_text=cleaned_text,
                        sentiment=sentiment_label,
                        confidence=confidence_score
                    )

                    st.success(f"✅ Phân tích hoàn tất!")

                    with st.container(border=True):
                        st.markdown(f"**📄 Câu đã nhập:** `{user_input}`")
                        st.markdown(f"**✨ Câu đã chuẩn hóa:** `{cleaned_text}`")

                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric(
                                label="**CẢM XÚC**",
                                value=sentiment_display["text"],
                                delta=f"{confidence_score:.1%} tin cậy"
                            )

                        with col_res2:
                            st.progress(
                                value=confidence_score,
                                text=f"Độ tin cậy: {confidence_score:.1%}"
                            )

                    color_hex = {
                        "green": "#28a745",
                        "red": "#dc3545",
                        "gray": "#6c757d",
                        "blue": "#007bff"
                    }[sentiment_display["color"]]

                    st.markdown(
                        f"""
                        <div style='
                            background-color: {color_hex}20; 
                            border-left: 5px solid {color_hex};
                            padding: 15px;
                            border-radius: 5px;
                            margin: 10px 0;
                        '>
                            <h4 style='color: {color_hex}; margin: 0;'>
                                {sentiment_display["text"]}
                            </h4>
                            <p style='margin: 5px 0 0 0;'>
                                Model dự đoán cảm xúc này với độ tin cậy <b>{confidence_score:.1%}</b>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi trong quá trình phân tích: {str(e)}")

    elif analyze_btn and not user_input:
        st.warning("⚠️ Vui lòng nhập câu cần phân tích!")

with col2:
    st.subheader("📜 Lịch sử phân loại")

    if st.button("🔄 Tải lại lịch sử", width='stretch'):
        st.rerun()

    try:
        history = db.get_recent_records(limit=10)

        if history:
            st.markdown("**50 bản ghi gần nhất:**")

            import pandas as pd

            display_data = []
            for i, record in enumerate(history, 1):
                sentiment_text = {
                    "POSITIVE": "😊 TÍCH CỰC",
                    "NEUTRAL": "😐 TRUNG TÍNH",
                    "NEGATIVE": "😞 TIÊU CỰC"
                }.get(record["sentiment"], record["sentiment"])

                display_data.append({
                    "STT": i,
                    "Câu": record["cleaned_text"][:30] + ("..." if len(record["cleaned_text"]) > 30 else ""),
                    "Cảm xúc": sentiment_text,
                    "Thời gian": record["timestamp"][11:16],
                    "Độ tin cậy": f"{record['confidence']:.0%}"
                })

            df = pd.DataFrame(display_data)
            st.dataframe(
                df,
                width='stretch',
                hide_index=True,
                column_config={
                    "STT": st.column_config.NumberColumn(width="small"),
                    "Câu": st.column_config.TextColumn(width="medium"),
                    "Cảm xúc": st.column_config.TextColumn(width="small"),
                    "Thời gian": st.column_config.TextColumn(width="small"),
                    "Độ tin cậy": st.column_config.TextColumn(width="small")
                }
            )

            if st.button("📋 Xem toàn bộ lịch sử", width='stretch'):
                all_history = db.get_all_records()
                if all_history:
                    st.write(f"Tổng cộng: {len(all_history)} bản ghi")
        else:
            st.info("📝 Chưa có lịch sử phân loại nào. Hãy thử phân tích một câu!")

    except Exception as e:
        st.error(f"❌ Lỗi khi tải lịch sử: {str(e)}")

    st.markdown("---")
    st.subheader("📈 Thống kê")

    try:
        stats = db.get_statistics()
        col_stat1, col_stat2 = st.columns(2)

        with col_stat1:
            st.metric("Tổng số phân tích", stats["total_records"])

        with col_stat2:
            if stats["total_records"] > 0:
                positive_rate = (stats["sentiment_counts"].get("POSITIVE", 0) / stats["total_records"]) * 100
                st.metric("Tỷ lệ tích cực", f"{positive_rate:.1f}%")
    except:
        pass

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col2:
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p><b>Trợ lý phân loại cảm xúc Tiếng Việt</b></p>
            <p>Ứng dụng sử dụng mô hình Transformer (PhoBERT) để phân loại cảm xúc</p>
            <p>Đồ án môn học - Seminar Chuyên Đề - © 2025</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if 'error' in st.session_state and st.session_state.error:
    st.error(st.session_state.error)
    st.session_state.error = None
