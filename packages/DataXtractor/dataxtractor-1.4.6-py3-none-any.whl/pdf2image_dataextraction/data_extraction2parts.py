import cv2
import os
import tempfile
import pytesseract
from pdf2image import convert_from_path
from typing import Union


def extract_text_from_image(image_path, language):
    extracted_text = pytesseract.image_to_string(
        image_path,
        lang=language,
    )
    return extracted_text


def DATA_EXTRACTION_2_PARTS(
    file_path: Union[str, os.PathLike],
    left_partition: float,
    right_partition: float,
    output_dir: Union[str, os.PathLike] = None,  # ✅ new optional param
    lang_part_first: str = "eng",
    lang_part_second: str = "eng",
):
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "split_images")

    left_folder = os.path.join(output_dir, "left")
    right_folder = os.path.join(output_dir, "right")
    os.makedirs(left_folder, exist_ok=True)
    os.makedirs(right_folder, exist_ok=True)

    first_part_text = ""
    second_part_text = ""

    def process_image(img, page_num=0):
        nonlocal first_part_text, second_part_text

        h, w, _ = img.shape

        left_cut = int(w * 0.01 * float(left_partition))
        right_cut = int(w * 0.01 * float(right_partition))

        left_part = img[:, :left_cut]
        right_part = img[:, -right_cut:]

        left_image_path = os.path.join(left_folder, f"left_{page_num + 1}.jpg")
        right_image_path = os.path.join(right_folder, f"right_{page_num + 1}.jpg")

        cv2.imwrite(left_image_path, left_part)
        cv2.imwrite(right_image_path, right_part)

        extracted_text_part_first = extract_text_from_image(
            left_image_path, lang_part_first
        )
        extracted_text_part_second = extract_text_from_image(
            right_image_path, lang_part_second
        )

        first_part_text += extracted_text_part_first
        second_part_text += extracted_text_part_second

    # Handle PDF
    if str(file_path).lower().endswith(".pdf"):
        images = convert_from_path(file_path)
        for i, page in enumerate(images):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_image_path = temp_file.name
                page.save(temp_image_path, "JPEG")
                img = cv2.imread(temp_image_path)
                process_image(img, i)
                os.remove(temp_image_path)
    else:
        # Handle image input
        img = cv2.imread(str(file_path))
        if img is None:
            raise ValueError(f"Unable to read image: {file_path}")
        process_image(img, 0)

    return first_part_text, second_part_text
