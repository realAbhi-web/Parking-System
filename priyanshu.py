import pytesseract
from PIL import Image
import os

# If you're using Windows, set the path to the tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'/home/abhinandan/Downloads/funny-message-license-plate_23-2150165791.webp'

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Example for Linux


import subprocess

# Test running tesseract directly
try:
    result = subprocess.run(['/usr/bin/tesseract', '--version'], capture_output=True, text=True)
    print("Tesseract Output:", result.stdout)
except Exception as e:
    print("Error running Tesseract:", str(e))

def convert_image_to_text(image_path):
    try:
        # Open the image file
        img = Image.open(image_path)
        
        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    # Specify the path to your image
    image_file = '/home/abhinandan/Downloads/funny-message-license-plate_23-2150165791.webp'  # Replace with your image file path
    print("Tesseract command path:", pytesseract.pytesseract.tesseract_cmd)
    
    # Convert the image to text
    extracted_text = convert_image_to_text(image_file)
    
    # Print the extracted text
    print("Extracted Text:")
    print(extracted_text)

