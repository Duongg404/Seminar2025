from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
import warnings
import streamlit as st

warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    def __init__(self, model_name="distilbert-base-multilingual-cased"):
        self.model_name = model_name
        self.device = 0 if torch.cuda.is_available() else -1

        self.classifier = None
        self._initialize_model()

    def _initialize_model(self):
        try:
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=self.device,
                truncation=True,
                max_length=256,
                framework="pt"
            )
            st.success("✅ Model đã được tải thành công!")
        except Exception as e:
            st.error(f"❌ Lỗi khi tải model: {e}")
            # Fallback model
            st.warning("⚠️ Đang sử dụng model fallback...")
            self.classifier = self._create_fallback_classifier()

    def _create_fallback_classifier(self):
        class FallbackClassifier:
            def __call__(self, text):
                return [{'label': 'NEUTRAL', 'score': 0.5}]
        return FallbackClassifier()

    def _map_sentiment_label(self, label):
        if not label:
            return "NEUTRAL"

        label = str(label).upper()

        if "POSITIVE" in label or "POS" in label or "1" in label:
            return "POSITIVE"
        elif "NEGATIVE" in label or "NEG" in label or "0" in label:
            return "NEGATIVE"
        elif "NEUTRAL" in label or "NEU" in label or "2" in label:
            return "NEUTRAL"
        else:
            return "NEUTRAL"
        pass

    def analyze(self, text, confidence_threshold=0.4):
        if not text or not isinstance(text, str) or len(text.strip()) < 2:
            return "NEUTRAL", 0.5

        try:
            if len(text) > 500:
                text = text[:500]

            result = self.classifier(text)

            if isinstance(result, list) and len(result) > 0:
                item = result[0]

                if isinstance(item, dict):
                    label = item.get('label', '')
                    score = item.get('score', 0.5)
                else:
                    label = str(item)
                    score = 0.5
            else:
                label = str(result) if result else ''
                score = 0.5

            mapped_label = self._map_sentiment_label(label)

            if (mapped_label != "NEUTRAL" and
                    isinstance(score, (int, float)) and
                    0 <= score <= 1 and
                    score < confidence_threshold):
                mapped_label = "NEUTRAL"
                score = max(score, 0.3)

            return mapped_label, float(score)

        except Exception as e:
            print(f"⚠️ Lỗi khi phân tích: {str(e)[:100]}")
            return "NEUTRAL", 0.5
        pass

    def batch_analyze(self, texts, confidence_threshold=0.4):
        results = []
        for text in texts:
            result = self.analyze(text, confidence_threshold)
            results.append(result)
        return results
        pass

    def get_model_info(self):
        return {
            "model_name": self.model_name,
            "device": "GPU" if self.device == 0 else "CPU",
            "max_length": 256
        }


# TEST MODULE
if __name__ == "__main__":
    print("🧪 Testing SentimentAnalyzer...")

    analyzer = SentimentAnalyzer()

    test_cases = [
        ("Hôm nay tôi rất vui", "POSITIVE"),
        ("Món ăn này dở quá", "NEGATIVE"),
        ("Thời tiết bình thường", "NEUTRAL"),
        ("Rat vui hom nay", "POSITIVE"),
        ("Công việc ổn định", "NEUTRAL"),
        ("Tôi ghét cái này", "NEGATIVE"),
        ("Tuyệt vời! Xuất sắc!", "POSITIVE"),
        ("Ngày mai họp lúc 9h", "NEUTRAL"),
        ("Buồn quá, mọi thứ thật tệ", "NEGATIVE"),
        ("Ổn, không có gì đặc biệt", "NEUTRAL")
    ]

    print("\n📊 Kết quả test:")
    print("=" * 80)

    correct = 0
    total = len(test_cases)

    for text, expected in test_cases:
        try:
            sentiment, confidence = analyzer.analyze(text, confidence_threshold=0.3)

            is_correct = sentiment == expected

            if is_correct:
                correct += 1

            status = "✅" if is_correct else "❌"
            print(f"{status} Text: '{text}'")
            print(f"   Expected: {expected:20} | Predicted: {sentiment:10} | Confidence: {confidence:.1%}")
            if not is_correct:
                print(f"   NOTE: Expected {expected}, got {sentiment}")
        except Exception as e:
            print(f"❌ Lỗi với text '{text}': {e}")

        print("-" * 80)

    accuracy = (correct / total) * 100 if total > 0 else 0
    print(f"\n📈 Tổng kết: {correct}/{total} đúng ({accuracy:.1f}%)")
