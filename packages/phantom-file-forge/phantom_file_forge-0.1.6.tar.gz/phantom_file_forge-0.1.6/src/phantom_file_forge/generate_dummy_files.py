#!/usr/bin/env python3

import argparse
import mimetypes
import os
import random
import string
import time
import uuid
import csv
import io
import zipfile
from PIL import Image, ImageDraw, ImageFont
import shutil

# --- Configuration ---
MIN_FILE_SIZE_GB = 1.0
MAX_FILE_SIZE_GB = 2.0
CHUNK_SIZE_BYTES = 1024 * 1024  # 1MB
NO_FILES = 10 # Number of files to generate

# Convert GB to Bytes
MIN_SIZE_BYTES = int(MIN_FILE_SIZE_GB * (1024**3))
MAX_SIZE_BYTES = int(MAX_FILE_SIZE_GB * (1024**3))

# Custom MIME type to extension and generator mapping
# This can override mimetypes.guess_extension or provide for types it doesn't know
CUSTOM_MIME_HANDLERS = {
    "text/plain": {"ext": ".txt", "generator": "_generate_dummy_txt"},
    "application/json": {"ext": ".json", "generator": "_generate_dummy_json"},
    "application/xml": {"ext": ".xml", "generator": "_generate_dummy_xml"},
    "text/xml": {"ext": ".xml", "generator": "_generate_dummy_xml"}, # Alias
    "text/csv": {"ext": ".csv", "generator": "_generate_dummy_csv"},
    "text/html": {"ext": ".html", "generator": "_generate_dummy_html"},
    "application/octet-stream": {"ext": ".bin", "generator": "_generate_dummy_binary"},
    "image/jpeg": {"ext": ".jpg", "generator": "_generate_dummy_jpeg"},
    "image/png": {"ext": ".png", "generator": "_generate_dummy_png"},
    "application/pdf": {"ext": ".pdf", "generator": "_generate_dummy_pdf"},
    "video/mp4": {"ext": ".mp4", "generator": "_generate_dummy_binary"},
    "application/zip": {"ext": ".zip", "generator": "_generate_dummy_binary"},
    "application/gzip": {"ext": ".gz", "generator": "_generate_dummy_binary"},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {"ext": ".docx", "generator": "_generate_dummy_docx"},
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {"ext": ".pptx", "generator": "_generate_dummy_pptx"},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {"ext": ".xlsx", "generator": "_generate_dummy_xlsx"},
    # Add more specific handlers if needed, otherwise they fall back to binary
}

# --- Helper Functions ---

def _get_random_printable_ascii_string(length):
    """Generates a random string of printable ASCII characters."""
    chars = string.ascii_letters + string.digits + string.punctuation + ' '
    return ''.join(random.choice(chars) for _ in range(length))

def _get_random_text_line(min_len=10, max_len=150):
    """Generates a random line of text."""
    return _get_random_printable_ascii_string(random.randint(min_len, max_len)) + '\n'

# --- Dummy Data Generators ---
# Each generator function takes (file_obj, total_size_to_write)

def _generate_dummy_binary(file_obj, total_size):
    """Generates random binary data."""
    bytes_written = 0
    while bytes_written < total_size:
        chunk = os.urandom(min(CHUNK_SIZE_BYTES, total_size - bytes_written))
        file_obj.write(chunk)
        bytes_written += len(chunk)

def _generate_dummy_txt(file_obj, total_size):
    """Generates dummy text data."""
    bytes_written = 0
    while bytes_written < total_size:
        line = _get_random_text_line().encode('utf-8', errors='ignore') # Ensure encoding
        # Ensure we don't write past total_size with the current line
        if bytes_written + len(line) > total_size:
            line = line[:total_size - bytes_written]
        if not line: # If trimming made it empty and we still need to write
             remaining = total_size - bytes_written
             line = (os.urandom(remaining) if remaining > 0 else b"")


        if line: # It might be empty if total_size was met exactly by previous chunks
            file_obj.write(line)
            bytes_written += len(line)
        if bytes_written >= total_size:
            break


def _generate_dummy_csv(file_obj, total_size):
    """Generates dummy CSV data."""
    # Use a TextIOWrapper for csv.writer, but underlying file_obj is binary
    # We will encode manually to control byte count more precisely.
    
    bytes_written = 0
    num_columns = random.randint(3, 10)
    
    # Header
    header = [_get_random_printable_ascii_string(random.randint(5,15)) for _ in range(num_columns)]
    header_line = (','.join(header) + '\n').encode('utf-8')
    
    if bytes_written + len(header_line) <= total_size:
        file_obj.write(header_line)
        bytes_written += len(header_line)
    else: # Not enough space even for header, fill with binary
        _generate_dummy_binary(file_obj, total_size)
        return

    row_count = 0
    while bytes_written < total_size:
        row_count += 1
        row_data = []
        for _ in range(num_columns):
            # Mix data types for CSV feel
            rand_val = random.random()
            if rand_val < 0.6: # String
                row_data.append(_get_random_printable_ascii_string(random.randint(5, 30)))
            elif rand_val < 0.9: # Integer
                row_data.append(str(random.randint(0, 100000)))
            else: # Float
                row_data.append(f"{random.uniform(0, 10000):.2f}")
        
        # Manually construct CSV line to control bytes
        # This simple join doesn't handle internal commas/quotes in data well,
        # but for dummy data, it's often acceptable. For robust CSV, use csv module
        # and write to a StringIO buffer first to measure size if precision is paramount.
        csv_line_str = ','.join(row_data) + '\n'
        csv_line_bytes = csv_line_str.encode('utf-8', errors='ignore')

        if bytes_written + len(csv_line_bytes) > total_size:
            remaining = total_size - bytes_written
            if remaining > 0:
                file_obj.write(csv_line_bytes[:remaining])
                bytes_written += remaining
            break 
        
        file_obj.write(csv_line_bytes)
        bytes_written += len(csv_line_bytes)
        
        if row_count % 1000 == 0: # Give some feedback for very large files
            print(f"  ... wrote {row_count} CSV rows, {bytes_written / (1024*1024):.2f} MB", end='\r')
    print(" " * 80, end='\r') # Clear line


def _generate_dummy_json(file_obj, total_size):
    """Generates dummy JSON data (a large array of objects)."""
    bytes_written = 0
    
    open_bracket = b"[\n"
    close_bracket = b"\n]\n"
    
    if bytes_written + len(open_bracket) < total_size :
        file_obj.write(open_bracket)
        bytes_written += len(open_bracket)
    else:
        _generate_dummy_binary(file_obj, total_size) # Not enough space
        return

    first_item = True
    item_count = 0
    while bytes_written < total_size - len(close_bracket) - 2 : # -2 for potential comma and newline
        item_count +=1
        obj = {
            "id": str(uuid.uuid4()),
            "index": item_count,
            "timestamp": time.time(),
            "random_string": _get_random_printable_ascii_string(random.randint(50, 200)),
            "random_number": random.randint(1, 1000000),
            "random_bool": random.choice([True, False]),
            "nested_obj": {
                "fieldA": _get_random_printable_ascii_string(10),
                "fieldB": random.random()
            }
        }
        # Use simple string formatting for JSON object, then encode.
        # Using json.dumps for each item is fine for structure, but slow for Gigs.
        # For massive scale, more optimized string building would be faster.
        item_str = f"  {{\n    \"id\": \"{obj['id']}\",\n    \"index\": {obj['index']},\n    \"message\": \"{obj['random_string'].replace('\"','\\\"')}\",\n    \"count\": {obj['random_number']}\n  }}"
        
        if not first_item:
            item_str = ",\n" + item_str
        
        item_bytes = item_str.encode('utf-8')

        if bytes_written + len(item_bytes) + len(close_bracket) > total_size:
            break # Next item would overflow

        file_obj.write(item_bytes)
        bytes_written += len(item_bytes)
        first_item = False

        if item_count % 100 == 0:
             print(f"  ... wrote {item_count} JSON objects, {bytes_written / (1024*1024):.2f} MB", end='\r')
    print(" " * 80, end='\r') # Clear line


    # Fill remaining space before close_bracket if any, with spaces or truncated data
    remaining_for_content = total_size - bytes_written - len(close_bracket)
    if remaining_for_content > 0:
        # Could add more minimal content, or just spaces for text-based
        filler = b' ' * remaining_for_content
        file_obj.write(filler)
        bytes_written += len(filler)
        
    file_obj.write(close_bracket)
    bytes_written += len(close_bracket)

    # If slightly under, pad with binary (though for JSON this makes it invalid)
    # Better to accept slight undersize for structured data to maintain validity.
    # Or, the item generation loop should be more precise.
    # For this dummy generator, "close enough" is usually fine.
    if bytes_written < total_size:
        _generate_dummy_binary(file_obj, total_size - bytes_written)

def _generate_dummy_png(file_obj, total_size):
    """
    Generates a minimal valid PNG file with random text rendered on the image,
    and pads it to the desired size. Requires Pillow.
    """

    # Estimate image size to roughly match total_size (very approximate)
    width, height = 512, 512

    # Create a white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Generate random text
    text = _get_random_printable_ascii_string(random.randint(20, 100))

    # Try to use a default font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Draw text in the center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill='black', font=font)

    # Save image to a BytesIO buffer as PNG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG', compress_level=6)
    png_data = img_buffer.getvalue()

    # If the image is smaller than total_size, pad with random data
    bytes_written = 0
    file_obj.write(png_data)
    bytes_written += len(png_data)

    if bytes_written < total_size:
        file_obj.write(os.urandom(total_size - bytes_written))


def _generate_dummy_jpeg(file_obj, total_size):
    """
    Generates a minimal valid JPEG file with random text rendered on the image,
    and pads it to the desired size. Requires Pillow.
    """

    # Estimate image size to roughly match total_size (very approximate)
    # 3 bytes per pixel for RGB, plus JPEG compression (so image will be smaller)
    # We'll use a fixed size and pad as needed.
    width, height = 512, 512

    # Create a white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Generate random text
    text = _get_random_printable_ascii_string(random.randint(20, 100))

    # Try to use a default font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Draw text in the center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill='black', font=font)

    # Save image to a BytesIO buffer as JPEG
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=85)
    jpeg_data = img_buffer.getvalue()

    # If the image is smaller than total_size, pad with random data
    bytes_written = 0
    file_obj.write(jpeg_data)
    bytes_written += len(jpeg_data)

    if bytes_written < total_size:
        file_obj.write(os.urandom(total_size - bytes_written))


def _generate_dummy_pdf(file_obj, total_size):
    """
    Generates a minimal valid PDF file and pads it to the desired size.
    The PDF will have a single page and some dummy text.
    """
    # Minimal PDF header and body
    header = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
    body = (
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length 44 >>\n"
        b"stream\n"
        b"BT /F1 24 Tf 100 700 Td (Dummy PDF content) Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000061 00000 n \n"
        b"0000000112 00000 n \n"
        b"0000000211 00000 n \n"
        b"trailer\n"
        b"<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n"
        b"312\n"
        b"%%EOF\n"
    )
    data = header + body
    file_obj.write(data)
    bytes_written = len(data)
    # Pad with zeros or random data to reach total_size
    if bytes_written < total_size:
        file_obj.write(os.urandom(total_size - bytes_written))


def _generate_dummy_xlsx(file_obj, total_size):
    """
    Generates a minimal valid XLSX file (Office Open XML Spreadsheet document) and pads it to the desired size.
    The XLSX format is a ZIP archive with specific XML files inside.
    """

    # Minimal XLSX structure (required files)
    xlsx_files = {
        '[Content_Types].xml': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            b'<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            b'</Types>'
        ),
        '_rels/.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            b'</Relationships>'
        ),
        'xl/_rels/workbook.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            b'</Relationships>'
        ),
        'xl/workbook.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets>'
            b'</workbook>'
        ),
        'xl/worksheets/sheet1.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b'<sheetData>'
            b'<row r="1"><c r="A1" t="inlineStr"><is><t>Dummy XLSX content</t></is></c></row>'
            b'</sheetData>'
            b'</worksheet>'
        ),
    }

    # Write minimal XLSX to a BytesIO buffer
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as xlsx_zip:
        for name, content in xlsx_files.items():
            xlsx_zip.writestr(name, content)
        # Add a large dummy part to quickly reach the target size
        # This is not strictly valid, but most XLSX readers ignore unknown files
        dummy_size = max(0, total_size - buffer.tell() - 1024)
        if dummy_size > 0:
            xlsx_zip.writestr('xl/media/dummy.bin', os.urandom(dummy_size))

    # Write the buffer to the output file
    data = buffer.getvalue()
    file_obj.write(data)
    bytes_written = len(data)

    # If still not enough, pad with zeros (rare, but possible due to zip overhead)
    if bytes_written < total_size:
        file_obj.write(b'\0' * (total_size - bytes_written))


def _generate_dummy_pptx(file_obj, total_size):
    """
    Generates a minimal valid PPTX file (Office Open XML Presentation document) and pads it to the desired size.
    The PPTX format is a ZIP archive with specific XML files inside.
    """

    # Minimal PPTX structure (required files for PowerPoint to open)
    pptx_files = {
        '[Content_Types].xml': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            b'<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            b'<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            b'<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            b'<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
            b'</Types>'
        ),
        '_rels/.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            b'</Relationships>'
        ),
        'ppt/_rels/presentation.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
            b'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
            b'</Relationships>'
        ),
        'ppt/presentation.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<p:sldMasterIdLst>'
            b'<p:sldMasterId id="2147483648" r:id="rId2"/>'
            b'</p:sldMasterIdLst>'
            b'<p:sldIdLst>'
            b'<p:sldId id="256" r:id="rId1"/>'
            b'</p:sldIdLst>'
            b'<p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>'
            b'<p:notesSz cx="6858000" cy="9144000"/>'
            b'</p:presentation>'
        ),
        'ppt/slides/slide1.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>'
            b'<p:clrMapOvr><a:masterClrMapping xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/></p:clrMapOvr>'
            b'</p:sld>'
        ),
        'ppt/slides/_rels/slide1.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            b'</Relationships>'
        ),
        'ppt/slideLayouts/slideLayout1.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            b'type="title">'
            b'<p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>'
            b'<p:clrMapOvr><a:masterClrMapping xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/></p:clrMapOvr>'
            b'</p:sldLayout>'
        ),
        'ppt/slideLayouts/_rels/slideLayout1.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
            b'</Relationships>'
        ),
        'ppt/slideMasters/slideMaster1.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            b'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            b'<p:cSld><p:spTree><p:nvGrpSpPr/><p:grpSpPr/></p:spTree></p:cSld>'
            b'<p:clrMap xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            b'bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            b'<p:sldLayoutIdLst>'
            b'<p:sldLayoutId id="1" r:id="rId1"/>'
            b'</p:sldLayoutIdLst>'
            b'</p:sldMaster>'
        ),
        'ppt/slideMasters/_rels/slideMaster1.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            b'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
            b'</Relationships>'
        ),
        'ppt/theme/theme1.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Dummy Theme">'
            b'<a:themeElements/>'
            b'</a:theme>'
        ),
    }

    # Write minimal PPTX to a BytesIO buffer
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as pptx_zip:
        for name, content in pptx_files.items():
            pptx_zip.writestr(name, content)
        # Add a large dummy part to quickly reach the target size
        # This is not strictly valid, but most PPTX readers ignore unknown files
        dummy_size = max(0, total_size - buffer.tell() - 1024)
        if dummy_size > 0:
            pptx_zip.writestr('ppt/media/dummy.bin', os.urandom(dummy_size))

    # Write the buffer to the output file
    data = buffer.getvalue()
    file_obj.write(data)
    bytes_written = len(data)

    # If still not enough, pad with zeros (rare, but possible due to zip overhead)
    if bytes_written < total_size:
        file_obj.write(b'\0' * (total_size - bytes_written))


def _generate_dummy_docx(file_obj, total_size):
    """
    Generates a minimal valid DOCX file (Office Open XML Word document) and pads it to the desired size.
    The DOCX format is a ZIP archive with specific XML files inside.
    """

    # Minimal DOCX structure (required files)
    docx_files = {
        '[Content_Types].xml': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            b'</Types>'
        ),
        '_rels/.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            b'</Relationships>'
        ),
        'word/_rels/document.xml.rels': (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
        ),
        'word/document.xml': (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b'<w:body>'
            b'<w:p><w:r><w:t>Dummy DOCX content</w:t></w:r></w:p>'
            b'</w:body>'
            b'</w:document>'
        ),
    }

    # Write minimal DOCX to a BytesIO buffer
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as docx_zip:
        for name, content in docx_files.items():
            docx_zip.writestr(name, content)
        # Add a large dummy part to quickly reach the target size
        # This is not strictly valid, but most DOCX readers ignore unknown files
        dummy_size = max(0, total_size - buffer.tell() - 1024)
        if dummy_size > 0:
            # Write a large file inside the zip to pad size
            docx_zip.writestr('word/dummy.bin', os.urandom(dummy_size))

    # Write the buffer to the output file
    data = buffer.getvalue()
    file_obj.write(data)
    bytes_written = len(data)

    # If still not enough, pad with zeros (rare, but possible due to zip overhead)
    if bytes_written < total_size:
        file_obj.write(b'\0' * (total_size - bytes_written))


def _generate_dummy_xml(file_obj, total_size):
    """Generates dummy XML data."""
    bytes_written = 0
    
    # Basic XML structure
    header = b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root>\n"
    footer = b"\n</root>\n"
    
    if bytes_written + len(header) < total_size:
        file_obj.write(header)
        bytes_written += len(header)
    else:
        _generate_dummy_binary(file_obj, total_size)
        return

    item_count = 0
    while bytes_written < total_size - len(footer) - 10: # -10 for buffer
        item_count +=1
        # Escape basic XML characters in data
        text_content = _get_random_printable_ascii_string(random.randint(100, 300))
        text_content = text_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        item_str = f"  <item id=\"{item_count}\" timestamp=\"{time.time():.0f}\">\n" \
                   f"    <uuid>{uuid.uuid4()}</uuid>\n" \
                   f"    <random_data>{text_content}</random_data>\n" \
                   f"    <value>{random.randint(0, 1000)}</value>\n" \
                   f"  </item>\n"
        item_bytes = item_str.encode('utf-8')

        if bytes_written + len(item_bytes) + len(footer) > total_size:
            break
            
        file_obj.write(item_bytes)
        bytes_written += len(item_bytes)

        if item_count % 100 == 0:
            print(f"  ... wrote {item_count} XML items, {bytes_written / (1024*1024):.2f} MB", end='\r')
    print(" " * 80, end='\r') # Clear line


    remaining_for_content = total_size - bytes_written - len(footer)
    if remaining_for_content > 0:
        # Could add more minimal content, or just spaces for text-based
        # For XML, a comment is safer:
        filler = (f"\n").encode('utf-8')
        if len(filler) > remaining_for_content : filler = filler[:remaining_for_content]
        file_obj.write(filler)
        bytes_written += len(filler)

    file_obj.write(footer)
    bytes_written += len(footer)
    
    if bytes_written < total_size:
        _generate_dummy_binary(file_obj, total_size - bytes_written)


def _generate_dummy_html(file_obj, total_size):
    """Generates dummy HTML data."""
    bytes_written = 0
    
    header = b"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>Dummy HTML Page</title>\n" \
             b"  <style>body { font-family: sans-serif; line-height: 1.6; margin: 20px; } " \
             b".content p { margin-bottom: 15px; } " \
             b".footer { margin-top: 50px; font-size: 0.8em; color: #777;}</style>\n" \
             b"</head>\n<body>\n<header><h1>Large Dummy HTML Document</h1></header>\n<main class=\"content\">\n"
    footer = b"\n</main>\n<footer class=\"footer\"><p>&copy; 2025 Dummy Data Inc.</p></footer>\n</body>\n</html>"

    if bytes_written + len(header) < total_size:
        file_obj.write(header)
        bytes_written += len(header)
    else:
        _generate_dummy_binary(file_obj, total_size)
        return

    para_count = 0
    while bytes_written < total_size - len(footer) - 20: # Buffer for last paragraph
        para_count +=1
        # Generate a few sentences for a paragraph
        num_sentences = random.randint(3, 7)
        paragraph_text = " ".join([_get_random_printable_ascii_string(random.randint(40,120)).capitalize() + "." for _ in range(num_sentences)])
        # Escape basic HTML characters
        paragraph_text = paragraph_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        para_str = f"  <p><strong>Paragraph {para_count}:</strong> {paragraph_text} {_get_random_printable_ascii_string(random.randint(200,500))}</p>\n"
        para_bytes = para_str.encode('utf-8', errors='ignore')

        if bytes_written + len(para_bytes) + len(footer) > total_size:
            break
        
        file_obj.write(para_bytes)
        bytes_written += len(para_bytes)
        
        if para_count % 50 == 0:
            print(f"  ... wrote {para_count} HTML paragraphs, {bytes_written / (1024*1024):.2f} MB", end='\r')
    print(" " * 80, end='\r') # Clear line

    remaining_for_content = total_size - bytes_written - len(footer)
    if remaining_for_content > 0:
        # Add filler text inside a <p> or as a comment
        filler_text = _get_random_printable_ascii_string(remaining_for_content - 10) # -10 for tags
        filler = f"<p>{filler_text}</p>\n".encode('utf-8')
        if len(filler) > remaining_for_content : filler = filler[:remaining_for_content]
        file_obj.write(filler)
        bytes_written += len(filler)

    file_obj.write(footer)
    bytes_written += len(footer)

    if bytes_written < total_size: # Pad if needed, though this might break strict HTML
        _generate_dummy_binary(file_obj, total_size - bytes_written)


# --- Main Logic ---
def generate_file(mime_type, output_dir="."):
    """Generates a single dummy file for the given MIME type."""
    
    print(f"\nProcessing MIME type: {mime_type}")

    target_size_bytes = random.randint(MIN_SIZE_BYTES, MAX_SIZE_BYTES)
    target_size_gb = target_size_bytes / (1024**3)
    print(f"  Target size: {target_size_gb:.2f} GiB ({target_size_bytes} bytes)")

    handler_info = CUSTOM_MIME_HANDLERS.get(mime_type)
    file_ext = None
    generator_func_name = "_generate_dummy_binary" # Default generator

    if handler_info:
        file_ext = handler_info.get("ext")
        generator_func_name = handler_info.get("generator", "_generate_dummy_binary")
    
    if not file_ext:
        # mimetypes.guess_extension might add a leading dot, ensure it's there
        guessed_ext = mimetypes.guess_extension(mime_type, strict=False) # strict=False for more guesses
        if guessed_ext:
            file_ext = guessed_ext if guessed_ext.startswith('.') else '.' + guessed_ext
        else:
            # Fallback extension if MIME type is unknown or has no common extension
            sanitized_mime_suffix = mime_type.split('/')[-1].replace('+', '_').replace('.', '_')
            file_ext = f".{sanitized_mime_suffix}.dat" 
            print(f"  Warning: Could not guess extension for {mime_type}, using fallback: {file_ext}")

    generator_func = globals().get(generator_func_name, _generate_dummy_binary)

    # Sanitize mime_type for filename
    safe_mime_name = mime_type.replace("/", "_").replace("+", "_")
    # Use a high-resolution timestamp and random suffix to avoid filename conflicts
    timestamp = f"{int(time.time())}_{random.randint(1000, 9999)}"
    filename = f"dummy_{safe_mime_name}_{timestamp}{file_ext}"
    filepath = os.path.join(output_dir, filename)

    print(f"  Generating file: {filepath}")
    print(f"  Using generator: {generator_func.__name__}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(filepath, "wb") as f: # Open in binary mode for all generators
            start_time = time.time()
            generator_func(f, target_size_bytes)
            end_time = time.time()
        
        actual_size = os.path.getsize(filepath)
        duration = end_time - start_time
        speed_mb_s = (actual_size / (1024*1024)) / duration if duration > 0 else float('inf')

        print(f"  Successfully generated: {filepath}")
        print(f"  Final size: {actual_size / (1024**3):.2f} GiB ({actual_size} bytes)")
        print(f"  Time taken: {duration:.2f} seconds ({speed_mb_s:.2f} MB/s)")

    except Exception as e:
        print(f"  Error generating file for {mime_type}: {e}")
        if os.path.exists(filepath): # Clean up partial file
            try:
                os.remove(filepath)
            except OSError as oe:
                print(f"  Error cleaning up partial file {filepath}: {oe}")
    return filepath

def main():
    # Declare upfront which module-level variables this function might rebind.
    global MIN_SIZE_BYTES, MAX_SIZE_BYTES, CHUNK_SIZE_BYTES, NO_FILES

    parser = argparse.ArgumentParser(
        description="Generate dummy files of specified MIME types with random sizes (1GB-2GB).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "mime_types",
        metavar="MIME_TYPE",
        type=str,
        nargs='+',
        help="One or more MIME types to generate files for (e.g., text/plain application/json image/jpeg)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=".",
        help="Directory to save generated files (default: current directory)."
    )
    parser.add_argument(
        "--min-gb",
        type=float,
        default=MIN_FILE_SIZE_GB, # Uses the module-level constant for default
        help=f"Minimum file size in GiB (default: {MIN_FILE_SIZE_GB})"
    )
    parser.add_argument(
        "--max-gb",
        type=float,
        default=MAX_FILE_SIZE_GB, # Uses the module-level constant for default
        help=f"Maximum file size in GiB (default: {MAX_FILE_SIZE_GB})"
    )
    parser.add_argument(
        "--chunk-mb",
        type=int,
        # This default correctly uses the initial module-level CHUNK_SIZE_BYTES
        default=CHUNK_SIZE_BYTES // (1024*1024),
        help=f"Chunk size in MiB for writing (default: {CHUNK_SIZE_BYTES // (1024*1024)})"
    )
    parser.add_argument(
        "--no-files",
        type=int,
        # This default correctly uses the initial module-level CHUNK_SIZE_BYTES
        default=NO_FILES // (10),
        help=f"Number of files to generate (default: {NO_FILES // (10)})"
    )

    args = parser.parse_args()

    # Now, we rebind the global variables using the parsed arguments.
    # The `global` declaration at the top ensures these are assignments to the global names.
    MIN_SIZE_BYTES = int(args.min_gb * (1024**3))
    MAX_SIZE_BYTES = int(args.max_gb * (1024**3))
    CHUNK_SIZE_BYTES = args.chunk_mb * (1024**2) # Convert MB from arg to bytes
    NO_FILES = args.no_files

    if MIN_SIZE_BYTES >= MAX_SIZE_BYTES:
        print("Error: Minimum size must be less than maximum size.")
        return

    print(f"File sizes will range from {args.min_gb:.2f} GiB to {args.max_gb:.2f} GiB.")
    print(f"Using chunk size: {args.chunk_mb} MiB (which is {CHUNK_SIZE_BYTES} bytes).")
    print(f"Using no fo files to be generated: {args.no_files} (which is {NO_FILES}).")


    for mime_type in args.mime_types:
        for file in range(NO_FILES):
            generate_file(mime_type, args.output_dir)

    # Compress the output directory into a zip file after all files are generated
    output_zip = os.path.abspath(args.output_dir.rstrip(os.sep)) + ".zip"
    print(f"\nCompressing output directory '{args.output_dir}' to '{output_zip}' ...")
    shutil.make_archive(os.path.splitext(output_zip)[0], 'zip', args.output_dir)
    print(f"Compression complete: {output_zip}")

    print("\nAll tasks completed.")

# --- (The rest of the script: imports, constants, helper functions, generators, etc. remains unchanged) ---

# Configuration (ensure these are defined before main)
MIN_FILE_SIZE_GB = 0.005
MAX_FILE_SIZE_GB = 0.008
# Initial CHUNK_SIZE_BYTES, which might be updated by command-line args via main()
CHUNK_SIZE_BYTES = 1024 * 1024  # 1MB

# Convert GB to Bytes (initial values, might be updated by command-line args via main())
MIN_SIZE_BYTES = int(MIN_FILE_SIZE_GB * (1024**3))
MAX_SIZE_BYTES = int(MAX_FILE_SIZE_GB * (1024**3))

# ... (all other functions like _get_random_printable_ascii_string, generators, generate_file)

if __name__ == "__main__":
    main()
