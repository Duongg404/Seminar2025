import re
import unicodedata
from typing import Dict, List

class VietnamesePreprocessor:
    def __init__(self):

        self.slang_dict = {
            " rat ": " rất ", " r ": " rất ", " rat' ": " rất ",
            " ko ": " không ", " k ": " không ", " kg ": " không ", " kh ": " không ",
            " dc ": " được ", " đc ": " được ", " đk ": " được ",
            " ng ": " người ", " n ": " người ",
            " mk ": " mình ", " m ": " mình ", " mjk ": " mình ",
            " bn ": " bạn ", " b ": " bạn ",
            " bt ": " bình thường ", " bthuong ": " bình thường ",
            " dep ": " đẹp ", " xau ": " xấu ", " xau' ": " xấu ",
            " ak ": " ạ ", " h ": " giờ ", " ti ": " tí ",

            " hom nay ": " hôm nay ", " hom qua ": " hôm qua ", " ngay mai ": " ngày mai ",
            " hom ": " hôm ", " ngay ": " ngày ", " thang ": " tháng ", " nam ": " năm ",
            " toi ": " tôi ", " tao ": " tôi ", " minh ": " mình ", " chao ": " chào ",
            " vui ": " vui ", " buon ": " buồn ", " buon` ": " buồn ",
            " cam on ": " cảm ơn ", " thanks ": " cảm ơn ", " thank you ": " cảm ơn ",
            " xin loi ": " xin lỗi ", " sorry ": " xin lỗi ",

            " fai ": " phải ", " pai ": " phải ",
            " zui ": " vui ", " zuiz ": " vui ",
            " thoai ": " thoải ", " thoi ": " thôi ", " thui ": " thôi ",
            " oi ": " ơi ", " ui ": " ơi ",

            " ui troi ": " trời ơi ", " uj troi ": " trời ơi ",
            " oh my god ": " trời ơi ", " omg ": " trời ơi ",
            " wtf ": " thật không thể tin nổi ", " lol ": " buồn cười ",
        }

        expanded_dict = {}
        for key, value in self.slang_dict.items():
            expanded_dict[key] = value

            if key.startswith(" "):
                expanded_dict[key[1:]] = value

            if key.endswith(" "):
                expanded_dict[key[:-1]] = value

            if key.startswith(" ") and key.endswith(" "):
                expanded_dict[key[1:-1]] = value

        self.slang_dict = expanded_dict

        self.pattern = re.compile(
            r'\b(' + '|'.join(re.escape(key) for key in self.slang_dict.keys()) + r')\b',
            re.IGNORECASE
        )

        self.clean_pattern = re.compile(
            r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ.,!?\-]',
            re.UNICODE)

        self.space_pattern = re.compile(r'\s+')

        print("✅ VietnamesePreprocessor đã sẵn sàng!")
        print(f"   - Số lượng từ trong từ điển: {len(self.slang_dict)}")

    def _replace_slang(self, match):
        word = match.group(0).lower()
        return self.slang_dict.get(word, word)

    def normalize_text(self, text):
        if not text or not isinstance(text, str):
            return ""

        text = unicodedata.normalize('NFC', text)

        text = text.lower()

        text = self.pattern.sub(self._replace_slang, text)

        text = self.clean_pattern.sub(' ', text)

        text = self.space_pattern.sub(' ', text)
        text = text.strip()

        text = re.sub(r'([.,!?])(\w)', r'\1 \2', text)

        return text

    def clean_text(self, text, max_length=200):

        text = self.normalize_text(text)

        if len(text) > max_length:
            cut_pos = text[:max_length].rfind(' ')
            if cut_pos > max_length // 2:
                text = text[:cut_pos] + "..."
            else:
                text = text[:max_length] + "..."

        return text

    def preprocess(self, text, max_length=200):
        return self.clean_text(text, max_length)

    def normalize(self, text):
        return self.normalize_text(text)

    def get_slang_dict_size(self):
        return len(self.slang_dict)

# TEST MODULE
if __name__ == "__main__":
    print("🧪 Testing VietnamesePreprocessor...")

    preprocessor = VietnamesePreprocessor()

    test_cases = [
        "  hom nay toi RAT vui, cam on ban nhieu   ",
        "toi ko thich mon an nay, no do qua!",
        "Rat vui hom nay, dc gap bn cu :)",
        "Công việc ổn định, mọi thứ bt",
        "Dep qua! toi thich cai nay nhat!!!",
        "wtf, cai gi vay? omg that k the tin noi"
    ]

    print("\n📝 Kết quả tiền xử lý:")
    print("-" * 80)
    for text in test_cases:
        cleaned = preprocessor.clean_text(text)
        print(f"Input:  '{text}'")
        print(f"Output: '{cleaned}'")
        print("-" * 80)

    print(f"\n📊 Thông tin preprocessor:")
    print(f"  - Số từ trong từ điển: {preprocessor.get_slang_dict_size()}")
