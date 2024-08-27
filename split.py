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

def save_image(image: Image.Image):
    path = "./test.jpg"
    image.save(path)

def get_image_size(image: Image.Image):
    return image.size

def is_not_white(image, x, y):
    pixel_value = image.getpixel((x, y))
    if pixel_value[0] != 255 and pixel_value[1] != 255 and pixel_value[2] != 255:
        return True
    return False

def get_slide_locations(image: Image.Image, slide_format):
    start_points = []
    image_size = get_image_size(image)

    if (slide_format == '2'):
        hori_middle = floor(image_size[0] / 2)
        vert_middle = floor(image_size[1] / 2)   

        one_third_down = floor(image_size[1] / 3)
        two_third_down = one_third_down * 2

        start_points.append([(hori_middle, 0),           (hori_middle, vert_middle),     (0, one_third_down),  (image_size[0]-1, one_third_down)])
        start_points.append([(hori_middle, vert_middle), (hori_middle, image_size[1]-1), (0, two_third_down), (image_size[0]-1, two_third_down)])
    elif (slide_format == '4sidebyside'):
        one_fourth_of_hori = floor(image_size[0] / 4)
        two_fourth_of_hori = one_fourth_of_hori * 2
        thr_fourth_of_hori = one_fourth_of_hori * 3

        one_sixth_of_vert = floor(image_size[1] / 6)
        two_sixth_of_vert = one_sixth_of_vert * 2
        thr_sixth_of_vert = one_sixth_of_vert * 3


        start_points.append([
            (one_fourth_of_hori, one_sixth_of_vert),
            (one_fourth_of_hori, thr_sixth_of_vert),
            (0, two_sixth_of_vert),
            (two_fourth_of_hori, two_sixth_of_vert),
        ])
        start_points.append([
            (thr_fourth_of_hori, one_sixth_of_vert),
            (thr_fourth_of_hori, thr_sixth_of_vert),
            (two_fourth_of_hori, two_sixth_of_vert),
            (image_size[0]-1, two_sixth_of_vert),
        ])

        one_seventh_of_vert = floor(image_size[1] / 7)
        fou_seventh_of_vert = one_seventh_of_vert * 4
        fiv_seventh_of_vert = one_seventh_of_vert * 5
        six_seventh_of_vert = one_seventh_of_vert * 6

        start_points.append([
            (one_fourth_of_hori, fou_seventh_of_vert),
            (one_fourth_of_hori, six_seventh_of_vert),
            (0, fiv_seventh_of_vert),
            (two_fourth_of_hori, fiv_seventh_of_vert),
        ])
        start_points.append([
            (thr_fourth_of_hori, fou_seventh_of_vert),
            (thr_fourth_of_hori, six_seventh_of_vert),
            (two_fourth_of_hori, fiv_seventh_of_vert),
            (image_size[0]-1, fiv_seventh_of_vert),
        ])
    else:
        print("Unknown format")
        exit

    slide_points = []
    for points in start_points:
        slide_location = get_slide_location(image, points)
        if -1 in slide_location:
            print(f"One of the coordinates wasn\'t found properly: {slide_location}, {points}")
            exit

        slide_points.append(slide_location)

    return slide_points

def get_slide_location(image: Image.Image, start_points):
    start_top, start_bottom, start_left, start_right = start_points

    top = -1
    for y in range(start_top[1], image_size[1]):
        if is_not_white(image, start_top[0], y):
            top = y
            break

    bottom = -1
    for y in range(start_bottom[1], 0, -1):
        if is_not_white(image, start_bottom[0], y):
            bottom = y
            break

    left = -1
    for x in range(start_left[0], image_size[0]):
        if is_not_white(image, x, start_left[1]):
            left = x
            break

    right = -1
    for x in range(start_right[0], 0, -1):
        if is_not_white(image, x, start_right[1]):
            right = x
            break

    return (top, bottom, left, right)

def convert_x_coord(size_multiplier, x):
    return round(x * size_multiplier, 2)

def convert_y_coord(size_multiplier, pdf_size, y):
    return round(pdf_size[1] - y * size_multiplier, 2)

def convert_coords(image_coords, image_size, pdf_size):
    size_multiplier_x = pdf_size[0] / image_size[0]
    size_multiplier_y = pdf_size[1] / image_size[1]

    new_coords = []
    for coords in image_coords:
        top, bottom, left, right = coords

        new_coords.append((
            convert_y_coord(size_multiplier_y, pdf_size, top),
            convert_y_coord(size_multiplier_y, pdf_size, bottom),
            convert_x_coord(size_multiplier_x, left),
            convert_x_coord(size_multiplier_x, right)
        ))

    return new_coords

def get_slides_on_page(page: PageObject, pdf_coords):
    slides = []
    for i in range(0, len(pdf_coords)-1):
        # FIXME: This is horribly slow, try with a different copying method
        slides.append(copy.deepcopy(page))
    slides.append(page)

    for i in range(0, len(pdf_coords)):
        slide = slides[i]
        top, bottom, left, right = pdf_coords[i]

        slide.mediabox.upper_right = (right, top)
        slide.mediabox.lower_left = (left, bottom)

    return slides

def write_pdf(output, pages):
    writer = PdfWriter()
    for page in pages:
        writer.add_page(page)
    writer.write(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transform PDF')

    parser.add_argument('input', type=str, help='Input PDF file')
    parser.add_argument('output', type=str, help='Output PDF file')
    parser.add_argument('--format', choices=['2', '4sidebyside'])

    args = parser.parse_args()

    pages = read_pdf(args.input)

    image = convert_page_to_image(pages[0])
    save_image(image)
    image_size = get_image_size(image)
    image_slide_locations = get_slide_locations(image, args.format)

    pdf_coords = convert_coords(image_slide_locations, image_size, pages[0].mediabox.upper_right)

    slides = []
    for page in pages:
        slides.extend(get_slides_on_page(page, pdf_coords))
    write_pdf(args.output, slides)


