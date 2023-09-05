import argparse
import copy
from pypdf import PdfWriter, PdfReader, PageObject
from pdf2image import convert_from_bytes
from io import BytesIO
from math import floor

from PIL import Image

def read_pdf(input):
    reader = PdfReader(input)
    return reader.pages

def convert_page_to_image(page: PageObject):
    pdf_bytes = BytesIO()

    writer = PdfWriter()
    writer.add_page(page)
    writer.write(pdf_bytes)

    images = convert_from_bytes(pdf_bytes.getvalue(), poppler_path='/usr/bin')
    return images[0]

def get_image_size(image: Image.Image):
    return image.size

def is_not_white(image, x, y):
    pixel_value = image.getpixel((x, y))
    if pixel_value[0] != 255 and pixel_value[1] != 255 and pixel_value[2] != 255:
        return True
    return False

def get_slide_locations(image: Image.Image):
    left = 0
    right = 0
    top_first_slide = 0
    bottom_first_slide = 0
    top_second_slide = 0
    bottom_second_slide = 0

    # Images start at top left corner
    image_size = get_image_size(image)

    # Start from left side about 1/3 down the page
    vert_start = image_size[1] / 3

    # We shouldnt need loop all the way over
    for x in range(image_size[0]):
        if is_not_white(image, x, vert_start):
            left = x
            break

    for x in range(image_size[0]-1, 0, -1):
        if is_not_white(image, x, vert_start):
            right = x
            break

    horizontal_start = floor(image_size[0] / 2)
    for y in range(0, image_size[0]):
        if is_not_white(image, horizontal_start, y):
            top_first_slide = y
            break

    for y in range(image_size[1]-1, 0, -1):
        if is_not_white(image, horizontal_start, y):
            bottom_second_slide = y
            break

    vertical_start = floor(image_size[1] / 2)
    for y in range(vertical_start, image_size[1]):
        if is_not_white(image, horizontal_start, y):
            top_second_slide = y
            break

    for y in range(vertical_start, 0, -1):
        if is_not_white(image, horizontal_start, y):
            bottom_first_slide = y
            break

    return (left, right, top_first_slide, bottom_first_slide, top_second_slide, bottom_second_slide)

def convert_coords(image_coords, image_size, pdf_size):
    img_left = image_coords[0]
    img_right = image_coords[1]
    img_sl1_top = image_coords[2]
    img_sl1_bottom = image_coords[3]
    img_sl2_top = image_coords[4]
    img_sl2_bottom = image_coords[5]

    size_multiplier_x = pdf_size[0] / image_size[0]
    size_multiplier_y = pdf_size[1] / image_size[1]

    # To convert simply subtract the y value from the height of the pdf
    pdf_left = round(img_left * size_multiplier_x, 2)
    pdf_right = round(img_right * size_multiplier_x, 2)
    pdf_sl1_top = round(pdf_size[1] - img_sl1_top * size_multiplier_y, 2)
    pdf_sl1_bottom = round(pdf_size[1] - img_sl1_bottom * size_multiplier_y, 2)
    pdf_sl2_top = round(pdf_size[1] - img_sl2_top * size_multiplier_y, 2)
    pdf_sl2_bottom = round(pdf_size[1] - img_sl2_bottom * size_multiplier_y, 2)

    return (pdf_left, pdf_right, pdf_sl1_top, pdf_sl1_bottom, pdf_sl2_top, pdf_sl2_bottom)

def get_slides_on_page(page: PageObject, pdf_coords):
    # FIXME: This is horribly slow, try with a different copying method
    slide1 = copy.deepcopy(page)
    slide2 = page

    left = pdf_coords[0]
    right = pdf_coords[1]

    slide1.mediabox.upper_right = (right, pdf_coords[2])
    slide1.mediabox.lower_left = (left, pdf_coords[3])

    slide2.mediabox.upper_right = (right, pdf_coords[4])
    slide2.mediabox.lower_left = (left, pdf_coords[5])

    return [slide1, slide2]

def write_pdf(output, pages):
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    writer.write(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform PDF')

    parser.add_argument('input', type=str, help='Input PDF file')
    parser.add_argument('output', type=str, help='Output PDF file')

    args = parser.parse_args()

    pages = read_pdf(args.input)

    image = convert_page_to_image(pages[0])
    image_size = get_image_size(image)
    img_sl_loc = get_slide_locations(image)

    pdf_coords = convert_coords(img_sl_loc, image_size, pages[0].mediabox.upper_right)

    slides = []
    for page in pages:
        slides.extend(get_slides_on_page(page, pdf_coords))
    write_pdf(args.output, slides)


