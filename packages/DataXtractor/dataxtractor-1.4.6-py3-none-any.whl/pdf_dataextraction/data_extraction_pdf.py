import pdftotext
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLineHorizontal
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1
import pandas as pd
from spire.xls import Workbook
import os
import numpy as np
import pdfplumber
from typing import List, Union
from pathlib import Path
import io


from image_dataextraction import data_imageextraction


def extract_text_from_pdf(pdf_file):
    text = ""
    with open(pdf_file, "rb") as file:
        pdf = pdftotext.PDF(file)
        for page in pdf:
            text += page
    return text


def extract_links_with_text(pdf_path):

    with open(pdf_path, "rb") as f:
        parser = PDFParser(f)
        doc = PDFDocument(parser)
        parser.set_document(doc)

        page_links = {}

        for page_num, page in enumerate(PDFPage.create_pages(doc), start=1):
            annots = page.annots
            if not annots:
                continue

            annotations = resolve1(annots)
            for annot in annotations:
                obj = resolve1(annot)
                if not isinstance(obj, dict):
                    continue

                uri = resolve1(obj.get("A")).get("URI") if obj.get("A") else None
                rect = obj.get("Rect")
                if uri and rect:
                    coords = tuple(resolve1(rect))
                    page_links.setdefault(page_num, []).append(
                        (uri.decode("utf-8") if isinstance(uri, bytes) else uri, coords)
                    )

    final_results = []
    for page_layout in extract_pages(pdf_path):
        page_num = page_layout.pageid
        if page_num not in page_links:
            continue

        for uri, (x0, y0, x1, y1) in page_links[page_num]:
            matching_text = []

            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    for line in element:
                        if isinstance(line, LTTextLineHorizontal):
                            lx0, ly0, lx1, ly1 = line.bbox
                            if lx0 < x1 and lx1 > x0 and ly0 < y1 and ly1 > y0:
                                matching_text.append(line.get_text().strip())

            full_text = " ".join(matching_text)
            final_results.append((page_num, uri, full_text))

    return final_results


def extract_tables_dynamic_pdf(
    pdf_input: Union[str, Path, bytes],
) -> List[pd.DataFrame]:
    """
    Extracts all tables from a PDF, regardless of structure.

    Parameters:
        pdf_input (str | Path | bytes): Path to the PDF or a bytes object.

    Returns:
        List[pd.DataFrame]: List of DataFrames, one per detected table.
    """
    tables = []

    # Handle file path or bytes input
    if isinstance(pdf_input, (str, Path)):
        pdf = pdfplumber.open(pdf_input)
    elif isinstance(pdf_input, bytes):
        pdf = pdfplumber.open(io.BytesIO(pdf_input))
    else:
        raise TypeError("Expected a file path or bytes input")

    for page_number, page in enumerate(pdf.pages, start=1):
        page_tables = page.extract_tables()
        print(page_tables)
        for table_index, raw_table in enumerate(page_tables):
            if not raw_table or not any(row for row in raw_table):
                continue

            df = pd.DataFrame(raw_table)

            if df.shape[0] > 1 and all(isinstance(v, str) for v in df.iloc[0]):
                df.columns = df.iloc[0]
                df = df[1:]

            df["__page__"] = page_number
            df["__table__"] = table_index + 1
            tables.append(df)

    pdf.close()
    return tables


def extract_table_from_xls(file, save_dir=None):
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")

    # ✅ Use user's save_dir or default to current working directory
    if save_dir is None:
        save_dir = os.path.join(os.getcwd(), "extracted_images")
    else:
        save_dir = os.path.abspath(save_dir)

    os.makedirs(save_dir, exist_ok=True)
    workbook = Workbook()
    workbook.LoadFromFile(file)

    sheet = workbook.Worksheets[0]
    image_list = data_imageextraction.extract_images_from_sheet(sheet, save_dir)

    workbook.Dispose()

    df = pd.read_excel(file, skiprows=8)
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    unnamed_6_groups = []
    current_group = []

    for index, row in df.iterrows():
        if not pd.isna(row["No."]):
            if current_group:
                unnamed_6_groups.append(current_group)
            current_group = [np.nan]

        if "Unnamed: 6" in df.columns and not pd.isna(row["Unnamed: 6"]):
            current_group.append(row["Unnamed: 6"])

    if current_group:
        unnamed_6_groups.append(current_group)

    df = df.drop(0)
    if "Unnamed: 6" in df.columns:
        df.drop(columns=["Unnamed: 6"], inplace=True)
    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    getlist = []
    index = 0

    for group in unnamed_6_groups[1:]:
        length_of_group = len(group)

        sliced_data = image_list[index : index + length_of_group]

        getlist.append(sliced_data)

        index += length_of_group

    positions_of_2740 = []

    for sublist in getlist:
        try:
            position = sublist.index(2740)
            positions_of_2740.append(position)
        except ValueError:
            positions_of_2740.append(None)

    df["Response"] = positions_of_2740

    return df
