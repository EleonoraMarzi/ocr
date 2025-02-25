from pdf2image import convert_from_path
import os
import ntpath
import cv2
import pytesseract
import numpy as np
import re

PDF_PATH = "/Users/andreapoltronieri/Documents/Assegno/Polifonia/WP4/Books/Dictionnaire_de_musique_Rousseau"
OUTPUT_PATH = "/Users/andreapoltronieri/Documents/Assegno/Polifonia/WP4/Books/"
OUTPUT_FORMAT = "png"
OUTPUT_NAME = "scanned.txt"
LANGUAGE = 'fra'


def file_info(file_path, out_path):
    """Takes as input the file input path and the output path and analyses the file name and the file extension.
    It also set a destination folder for the conversion from pdf to image."""
    file_name = ntpath.basename(file_path)
    file_name_no_ext = os.path.splitext(file_name)[0]
    file_ext = os.path.splitext(file_name)[1]
    results_path = out_path + file_name_no_ext

    return file_name_no_ext, file_ext, results_path


def pdf_to_img(file_path, out_path, out_format="png"):

    file_name_no_ext, file_ext, results_path = file_info(file_path, out_path)
    # check if exists a folder with the same name of the input file. If not, create one.
    if not os.path.isdir(results_path):
        os.makedirs(results_path)
    else:
        pass
    pages = convert_from_path(file_path, 500)

    page_num = 0
    for page in pages:
        page_num += 1
        page.save("{}/{}.{}".format(results_path, page_num, out_format), out_format)
        print("SAVING IMAGE: {}".format(page))


def image_processing(input_path, gray_scale=True, remove_noise=True, tresholding=True, dilate=True, erosion=True, edge_detection=True, skew_correction=True):
    kernel = np.ones((5, 5), np.uint8)
    image = cv2.imread(input_path)
    if gray_scale:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if remove_noise:
        image = cv2.medianBlur(image, 5)
    if tresholding:
        image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    if dilate:
        image = cv2.dilate(image, kernel, iterations=1)
    if erosion:
        image = cv2.erode(image, kernel, iterations=1)
    if edge_detection:
        image = cv2.Canny(image, 100, 200)
    if skew_correction:
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return image

# open image without columns
#text_result = pytesseract.image_to_string(Image.open(r'C:\Users\Utente\Documents\Polifonia\OCR\materiale da scannerizzare\ArpaOriginale\Arpa-1853-025-1.jpg'), lang='ita')


def ocr(processed_image, language):
    custom_config = r'--oem 3 --psm 6'
    ocr_output = pytesseract.image_to_string(processed_image, config=custom_config, lang=language)
    return ocr_output

# alternative code to process multilingual text 
# List of available languages
# print(pytesseract.get_languages(config=''))
def ocr(processed_image):
    custom_config = r'-l fra+eng+ita+spa --psm 6'    # code for 4 languages : italian, french, english, spanish
    ocr_output = pytesseract.image_to_string(img, config=custom_config)
    return ocr_output
    
def save_to_txt(out_name, ocr_res):
    f = open(out_name, 'w')
    f.write(ocr_res)
    f.close()


if __name__ == "__main__":
    file_name, extension, final_path = file_info(PDF_PATH, OUTPUT_PATH)
    if extension == ".pdf" and final_path:
        pass
        print("The input file is a .pdf file. Converting to image in {} format.".format(OUTPUT_FORMAT))
        pdf_to_img(PDF_PATH, OUTPUT_PATH, OUTPUT_FORMAT)
    else:
        # final_path = PDF_PATH
        print("THE DESTINATION FOLDER IS NOT EMPTY. PROCESSING THE FILES CONTAINED IN IT.")

    print("PROCESSING FOLDER: {}".format(final_path))

    ocr_all = ""

    for path, dirs, images in os.walk(final_path):
        for image in sorted(images, key=lambda f: int(re.sub('\D', '1', f))):
            filename, file_extension = os.path.splitext(image)
            if file_extension == ".{}".format(OUTPUT_FORMAT):
                print("PROCESSING IMAGE: {}/{}".format(path, image))

                image = image_processing("{}/{}".format(path, image))
                image_ocr = ocr(image, LANGUAGE)
            else:
                print("UNABLE TO PROCESS FILE: {}".format(image))
                continue

            ocr_all = ocr_all + "\n" + image_ocr

    save_to_txt(file_name + ".txt", ocr_all)
