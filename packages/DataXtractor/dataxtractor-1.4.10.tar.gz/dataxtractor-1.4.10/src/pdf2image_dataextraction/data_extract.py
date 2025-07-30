import cv2
import os
import tempfile
import pytesseract
from pdf2image import convert_from_path


def extract_text_from_image(image_path):
    extracted_text = pytesseract.image_to_string(
        image_path,
    )
    return extracted_text


def DATA_EXTRACTION(
    pdf_path,
):
    extacted_data = ""
    images = convert_from_path(pdf_path)

    for page_num, image in enumerate(images):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            image_path = temp_file.name
            image.save(image_path, "JPEG")

            extracted_text = extract_text_from_image(image_path)
            extacted_data += extracted_text

            temp_file.close()
            os.remove(image_path)

    return extacted_data
