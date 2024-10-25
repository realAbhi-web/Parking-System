import cv2
import pytesseract

# Path to the Tesseract executable (required on Windows, not required on Linux if installed globally)
# Example for Windows (make sure the path points to your Tesseract installation):
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

harcascade = "haarcascade_russian_plate_number.xml"
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

min_area = 500
count = 0

while True:
    success, img = cap.read()

    plate_cascade = cv2.CascadeClassifier(harcascade)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)

    for (x, y, w, h) in plates:
        area = w * h

        if area > min_area:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, "Number Plate", (x, y - 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 0, 255), 2)

            img_roi = img[y:y + h, x:x + w]  # Extract the region of interest (number plate area)
            cv2.imshow("ROI", img_roi)

            # Perform OCR on the ROI (detected plate area)
            plate_text = pytesseract.image_to_string(img_roi, config='--psm 8')  # Use PSM 8 for single-line OCR
            print("Detected Number Plate Text: ", plate_text)

    cv2.imshow("Result", img)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Save the number plate when 's' is pressed
    if cv2.waitKey(1) & 0xFF == ord('s'):
        cv2.imwrite("plates/scanned_img_" + str(count) + ".jpg", img_roi)
        cv2.rectangle(img, (0, 200), (640, 300), (0, 255, 0), cv2.FILLED)
        cv2.putText(img, "Plate saved", (150, 265), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
        cv2.imshow("Results", img)
        cv2.waitKey(500)
        count += 1

cap.release()
cv2.destroyAllWindows()
