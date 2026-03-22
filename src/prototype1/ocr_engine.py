import easyocr


class OCREngine:
    def __init__(self, languages=None):
        self.languages = languages or ["ar", "en"]
        self.reader = easyocr.Reader(self.languages, gpu=False)

    def read_text(self, img):
        results = self.reader.readtext(
            img,
            detail=1,
            paragraph=False,
        )

        texts = []
        confidences = []

        for (_, text, conf) in results:
            texts.append(text)
            confidences.append(conf)

        combined = " ".join(texts).strip()

        avg_conf = 0.0
        if confidences:
            avg_conf = sum(confidences) / len(confidences)

        return combined, avg_conf
