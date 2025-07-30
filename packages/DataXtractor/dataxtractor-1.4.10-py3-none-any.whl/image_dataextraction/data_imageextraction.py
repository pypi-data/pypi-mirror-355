import pytesseract
from PIL import Image
from spire.xls import XlsBitmapShape
import os


def Image_extraction(file_path):
    extract_data = pytesseract.image_to_string(Image.open(file_path))

    return extract_data


def extract_images_from_sheet(sheet, save_dir, desired_size_in_bytes=2740):
    os.makedirs(save_dir, exist_ok=True)

    image_list = []
    count = 0
    arrNum = []

    for i in range(sheet.Pictures.Count):
        try:
            pic = sheet.Pictures[i]
            if isinstance(pic, XlsBitmapShape):
                image_stream = pic.Picture
                image_data = image_stream.ToArray()
                image_size = len(image_data)
                image_list.append(image_size)

                if image_size == desired_size_in_bytes:
                    arrNum.append(count)
                    count = count + 1 if count < 3 else 0

                    image_filename = f"image_{i}_size_{image_size}.png"
                    image_path = os.path.join(save_dir, image_filename)

                    with open(image_path, "wb") as f:
                        f.write(image_data)
                else:
                    count = count + 1 if count < 3 else 0
            else:
                print(f"Picture {i} is not a valid bitmap shape.")
        except Exception as e:
            print(f"Error processing picture {i}: {e}")

    return image_list
