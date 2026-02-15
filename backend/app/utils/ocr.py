#import easyocr
try:
    import easyocr
except Exception:
    easyocr = None

import cv2

# load reader once
_reader = easyocr.Reader(['en'], gpu=False) if easyocr else None



def extract_text_from_image(path: str) -> str:
    if _reader is None:
        print("OCR disabled on deployment")
        return ""

    try:
        # read image
        img = cv2.imread(path)
        if img is None:
            print("Image not found:", path)
            return ""

        # improve OCR accuracy
        img = cv2.resize(img, None, fx=2, fy=2)

        # OCR
        results = _reader.readtext(img, detail=0)

        return " ".join(results)

    except Exception as e:
        print("OCR error:", e)
        return ""
