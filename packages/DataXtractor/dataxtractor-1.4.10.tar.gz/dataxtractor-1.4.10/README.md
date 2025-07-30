# DataXtractor Library

DataXtractor is a versatile library designed to extract text from PDF documents, with the ability to handle images and multi-column layouts. This README file provides an overview of the library's capabilities and how to use it effectively.

## Features

DataXtractor library offers the following key features:

### 1. Image to Text Extraction

DataXtractor is equipped to handle PDFs containing images. It utilizes Optical Character Recognition (OCR) to convert images embedded in PDF files into machine-readable text. This allows you to access and manipulate the textual content within images present in your PDF documents.

### 2. Multi-Column Text Extraction

In case your PDF contains text arranged in multiple columns, DataXtractor allows you to extract this text intelligently. The library can separate and extract content from each column independently, making it possible to obtain text in a structured and organized manner.

### 3. Language Support

DataXtractor supports multiple languages for OCR operations. You can specify the language code string using the `lang` parameter. By default, the library uses English (`eng`) if the language is not specified. You can also specify multiple languages for a more comprehensive text extraction process. For example:

```
```
supported_language_codes = [
    "ara", "aze", "aze_cyrl", "bel", "ben", "bod", "bos", "bul", "cat", "ceb", "ces", "chi_sim", "chi_sim_vert", "chi_tra",
    "chi_tra_vert", "chr", "cym", "dan", "deu", "deu-frak", "ell", "eng", "enm", "epo", "est", "eus", "fas", "fil", "fin",
    "fra", "frk", "frm", "fry", "gle", "glg", "grc", "guj", "hat", "heb", "hin", "hrv", "hun", "hye", "iku", "ind", "isl",
    "ita", "ita-old", "jav", "jpn", "jpn_vert", "kan", "kat", "kat-old", "kaz", "khm", "kir", "kor", "kor_vert", "lao",
    "lat", "lav", "lit", "ltz", "mal", "mar", "mkd", "mlt", "mon", "mri", "msa", "mya", "nep", "nld", "nor", "oci", "ori",
    "osd", "pan", "pol", "por", "pus", "ron", "rus", "san", "sin", "slk", "slv", "snd", "spa", "spa_old", "sqi", "srp",
    "srp_latn", "sun", "swa", "swe", "syr", "tam", "tat", "tel", "tgk", "tha", "tir", "ton", "tur", "uig", "ukr", "urd",
    "uzb", "uzb_cyrl", "vie", "yid", "yor"
]

```
```

This is especially useful when working with PDFs that contain text in various languages.

### 4. PDF Text Extraction

DataXtractor is not limited to image-based PDFs. It can also extract text directly from PDF documents that contain text content. This feature allows you to process PDF files, whether they contain text alone or a combination of text and images.

## Getting Started

To get started with the DataXtractor library, follow these steps:

1. **Installation**: Install the DataXtractor library by using the provided package manager (if available), or manually include it in your project.

2. **Library Initialization**: Initialize the DataXtractor library in your code, specifying the language(s) to use for OCR, as well as any other required parameters.

3. **PDF Processing**: Load your PDF document and apply the appropriate extraction functions based on your needs. For image-based PDFs, use OCR to convert images to text. For text-based PDFs, extract text directly.

4. **Output Handling**: Receive the extracted text and use it as needed for further processing or analysis within your application.

## You can convert a PDF into an image and then perform OCR on that image using two different languages. Additionally, you can crop the image into two parts for separate OCR processing.

## Example

```python
from pdf2image_dataextraction import data_extraction2parts


path = "sample.pdf"
left_partition = "40"
right_partition = "60"
lang_part_first = "en"
lang_part_second = "en"
data = data_extraction2parts.DATA_EXTRACTION_2_PARTS(
    path, left_partition, right_partition, lang_part_first, lang_part_second
)
print(data)

```

## Extract table from Xls if there is any image found in xls then its also work
## It require python 3.10 version
```python
from pdf_dataextraction import data_extraction_pdf


path = "sample.xls"
data = data_extraction_pdf.extract_table_from_xls(
    path,
    "/home/rahul.katoch/Desktop/Test/",
)
print(data)

```


## You can also extract data from PDF

```python
from pdf_dataextraction import data_extraction_pdf


path = "sample.pdf"
data = data_extraction_pdf.extract_text_from_pdf(path)
print(data)


```

## Extract table from pdf

```python
from pdf_dataextraction import data_extraction_pdf


path = "sample.pdf"
data = data_extraction_pdf.extract_tables_dynamic_pdf(path)
print(data)


```
## Extract links from the pdf
```python 

path = "sample.pdf"
data = data_extraction_pdf.extract_links_with_text(path)
print(data)

```


## You can also extract data from images
## Add this into your root
```python      
sudo apt install tesseract-ocr-all
```

```python
from image_dataextraction import data_imageextraction


path = "sample.jpeg"

data = data_imageextraction.Image_extraction(path)
print(data)

```

## Extract  Images form XLS

```python
from image_dataextraction import data_imageextraction


sheet = "sample.xls"
save_dir="./output"

image_list = data_imageextraction.extract_images_from_sheet(sheet, save_dir)
print(image_list)

```

## Contribute

If you find any issues or want to contribute to the DataXtractor library, please check the project's repository for information on how to get involved.

## License

This library is released under the [MIT License](LICENSE) to encourage collaboration and use in various applications.

---

DataXtractor is a powerful library for extracting text from PDF documents, whether they contain images, multi-column layouts, or plain text. It supports multiple languages and can be a valuable tool for text extraction and data analysis in a wide range of applications.
