from flask import Flask, render_template, request, url_for, redirect, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from api import rto_info, twilio_call, process_image
from priyanshu import convert_image_to_text
import http.client
import json
import os
import pytesseract
from PIL import Image
import base64
import io
import numpy as np
import cv2
import traceback
from io import BytesIO
import requests
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

UPLOAD_FOLDER = os.path.join('static', 'images')

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"  # Set to your correct path


def clear_terminal():
    if os.name == 'nt':  # If the operating system is Windows
        os.system('cls')
    else:  # If it's Linux or macOS
        os.system('clear')

# Example usageit
# clear_terminal()



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")  # Fetching from environment variables
app.secret_key = os.getenv("SECRET_KEY") 
db=SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
car_dictionary={}



class Users(db.Model, UserMixin):
      id = db.Column(db.Integer, primary_key=True)
      name=db.Column(db.String(100), nullable=True)
      car_owner_name=db.Column(db.String(30))
      number_plate=db.Column(db.String,unique=True,nullable=False)
      phone_number=db.Column(db.String,unique=True)
      email=db.Column(db.String)
      car_model=db.Column(db.String)
      password=db.Column(db.String)
      fuel_type=db.Column(db.String(30))
      engine_number=db.Column(db.String(50))
      insurance_upto=db.Column(db.String(20))
      insurance_company=db.Column(db.String(30))
      vehicle_color=db.Column(db.String(10))
      seat_capacity=db.Column(db.String(10))
      manufacturing_time=db.Column(db.String(20))
      criminal_activity=db.Column(db.Boolean, default=False)
      emergency_contact=db.Column(db.String(20), nullable=True)
      is_admin = db.Column(db.Boolean, default=False)



# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


@app.route("/emergency_call", methods=["GET", "POST"])
def emergency_call():
    # clear_terminal()
    print("we are in emergency function")
    if request.method == "POST":
        car_dictionary = session.get('car_dictionary', {})
        emergency_number = car_dictionary.get("emergency_contact")
        print("we are in first if")
        # if emergency_number:
        try:
            print("We are in try")
            msg=twilio_call(emergency_number)
            print("twilio call function has been made")
            print(msg)
            # flash("Emergency call initiated successfully.", "success")
        except Exception as e:
            print("An error occured while twilio cal", e)
        # else:
        #     flash("Emergency contact number not found.", "danger")
        #     print("we are in else block WARNING!")
        
    return redirect(url_for("home_page"))


@app.route("/")
def home_page():
    return render_template('index.html')

def convert_base64_to_image(base64_string):
    image_data = base64.b64decode(base64_string.split(',')[1])  # Decode base64
    np_arr = np.frombuffer(image_data, np.uint8)  # Convert binary data to numpy array
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Convert to OpenCV image
    return img


def convert_image_to_text(image):
    try:
        text = pytesseract.image_to_string(image, config='--psm 8')  # Tesseract OCR
        return text
    except Exception as e:
        return str(e)
    
@app.route("/photo")
def photo_page():
    return render_template("photo.html")

def process_image_base64(image_base64):
    
    try:
        # Convert base64 image to OpenCV format
        img = convert_base64_to_image(image_base64)

        # Convert to grayscale (this is important for many image processing tasks)
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Load the pre-trained Haar Cascade for number plate detection
        plate_cascade = cv2.CascadeClassifier('cascades/haarcascade_russian_plate_number.xml')

        if plate_cascade.empty():
            return {'error': 'Cascade classifier not found'}

        # Detect plates in the grayscale image
        plates = plate_cascade.detectMultiScale(img_gray, 1.1, 4)

        # If no plates are detected, return an error
        if len(plates) == 0:
            return {'plate_text': "No plate detected"}

        # For each detected plate, extract the region of interest (ROI) and apply OCR
        for (x, y, w, h) in plates:
            img_roi = img[y:y + h, x:x + w]  # Region of interest
            plate_text = convert_image_to_text(img_roi)  # Extract text from the ROI

        # Return the detected plate text
        return {'plate_text': plate_text}

    except Exception as e:
        print(f"Error processing image: {e}")
        traceback.print_exc()
        return {'error': 'Failed to process image'}

API_URL = "http://www.ocrwebservice.com/restservices/processDocument"
API_LICENSE_KEY = "ECC8AB9D-01D4-4750-A099-316B6760737D"  # Your license key
API_USERNAME = "ABHINANDAN"  # Your username

@app.route('/process_image', methods=['POST'])
def process_image():
    data = request.get_json()
    image_file = '/home/abhinandan/Code/Git/static/Images/Captured_Image.png'  # Replace with your image file path
    print("Tesseract command path:", pytesseract.pytesseract.tesseract_cmd)
    
    # Convert the image to textt
    extracted_text = convert_image_to_text(image_file)
    print(extracted_text)
    
    
    if 'image' not in data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Decode the base64 image (removing the data URL scheme: 'data:image/png;base64,')
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convert the image bytes into a PIL Image
        image = Image.open(BytesIO(image_bytes))
        
        # Generate a unique filename (for example using time)
        filename = 'captured_image.png'  # You can also use a unique identifier for each image
        
        # Save the image to the static/images folder
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)

        # You can now access the image like this: http://localhost:5000/static/images/captured_image.png
        image_url = url_for('static', filename=f'images/{filename}', _external=True)

        # Perform OCR or any other image processing here
        
        # For this example, let's just return the image URL
        return jsonify({'image_url': image_url, 'plate_text': 'Sample Plate Text'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/process_image', methods=['POST'])
# def handle_image():
#     if request.method == 'POST':
#         try:
#             # Retrieve the image from the JSON payload
#             data = request.json.get('image')  # Base64 encoded image

#             if not data:
#                 return jsonify({"error": "No image data provided"}), 400

#             # Process the image using the function from api.py
#             return process_image()

#         except Exception as e:
#             return jsonify({"error": str(e)}), 500

#     return render_template("photo.html")

@app.route('/twilio_click', methods=["GET","POST"])
def call():
    car_dictionary = session.get('car_dictionary', {})
    
    # Check for the phone_number before trying to call
    phone_number = car_dictionary.get("phone_number")
    message=twilio_call(phone_number)

    return message

@app.route("/contact-us",methods=["GET","POST"])
def contact():
    return render_template("contact.html")


@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Access denied", "danger")
        return redirect(url_for("home_page"))
    
    users = Users.query.all()
    return render_template("admin_dashboard.html", users=users)


@app.route("/tag_criminal/<int:user_id>", methods=["POST"])
def tag_criminal(user_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        flash("Access denied", "danger")
        return redirect(url_for("home_page"))
    
    user = Users.query.get_or_404(user_id)
    user.criminal_activity = not user.criminal_activity  # Toggle criminal status
    db.session.commit()
    flash(f"Car {user.number_plate} criminal status updated.", "success")
    return redirect(url_for("admin_dashboard"))



@app.route('/form', methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # Get the number plate from the form and convert it to uppercase
        number_plate = request.form.get("form-page-number-plate").lower()
        print(f"Searching for number plate: {number_plate}")  # Debugging output
        
        # Try to find the user in the database
        user = Users.query.filter_by(number_plate=number_plate).first()
        
        # Initialize car_dictionary to store the information
        car_dictionary = {}

        if user is not None:  # If user is found in the database
            # Populate car_dictionary with user data from the database
            car_dictionary = {
                "car_model": user.car_model,
                "owner_name": user.name,
                "fuel_type": user.fuel_type,
                "number_plate": user.number_plate,
                "engine_number": user.engine_number,
                "insurance_upto": user.insurance_upto,
                "insurance_company": user.insurance_company,
                "vehicle_color": user.vehicle_color,
                "seat_capacity": user.seat_capacity,
                "manufacturing_time": user.manufacturing_time,
                "phone_number": user.phone_number,
                "criminal_activity": user.criminal_activity 
            }
            print("Data found in database:", car_dictionary)
        else:  # If user is not found, call the API
            car_dictionary = rto_info(number_plate)  # Fetch data from the API
            print("Data fetched from API:", car_dictionary)

        # Store the result in the session
        session['car_dictionary'] = car_dictionary

        # Render the search.html template with the car_dictionary data
        return render_template("search.html", car_dictionary=car_dictionary)

    # Render the form page for GET requests
    return render_template('form.html')



@app.route("/home")
def log_in_user_page():
    return render_template('home.html')

# @app.route("/log_in", methods=["GET","POST"])
# def log_in():
#     if request.method=="POST":
#         user = Users.query.filter_by(email=request.form.get("email-log-in-form")).first()
#         # Check if the password entered is the 
#         # same as the user's password
#         if user.password == request.form.get("password-log-in-form"):
#             # Use the login_user method to log in the user
#             login_user(user)
#             flash('You have been logged in ,',user.name)
#             # print(user)
#             return redirect(url_for("home_page"))
#         else:
#             error="invalid email or password"
#             return render_template("log_in.html",error=error)


#     return render_template("log_in.html")

@app.route("/log_in", methods=["GET", "POST"])
def log_in():
    if request.method == "POST":
        try:
            # Retrieve user by email           
            user = Users.query.filter_by(email=request.form.get("email-log-in-form")).first()
            
            # If user exists and password matches
            if user and user.password == request.form.get("password-log-in-form"):
                login_user(user)  # Log the user in
                # flash(f'Welcome, {user.name}! You have been logged in.', 'success')
                print("log in succesful")
                print(user.name)
                print(user.is_admin)
                if user.is_admin:
                    print("user is admin for login ")
                    return redirect(url_for("admin_dashboard"))  
                return redirect(url_for("log_in_user_page"))
            else:
                # If login credentials are invalid
                flash("Invalid email or password", "danger")
                return render_template("log_in.html")
        
        except Exception as e:
            # Handle any unexpected errors
            print(e)
            flash(f"An error occurred: {str(e)}", "danger")
            return render_template("log_in.html")

    # Render login page for GET requests
    return render_template("log_in.html")



# @app.route("/sign_up", methods=["GET", "POST"])
# def sign_up():
#     if request.method == "POST":
#         user = Users(
#             name=request.form.get("name-form"),
#             number_plate=request.form.get("number-plate-form").lower(),  # Convert to uppercase here
#             phone_number=request.form.get("phone-number-form"),
#             email=request.form.get("email-address-form"),
#             car_model=request.form.get("car-form").lower(),  # Make sure car_model is also in uppercase
#             password=request.form.get("password-form")  # Make sure to save the password
#         )
#         db.session.add(user)
#         print("User added:")
#         print("Number Plate:", user.number_plate)  # This should now be uppercase
#         print("Phone Number:", user.phone_number)
#         db.session.commit()
#         return redirect("/")
#     return render_template("Sign_up.html")
@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    # clear_terminal()
    if request.method == "POST":
        email = request.form.get("email-address-form")
        domain = email.split("@")[-1]
        if domain in ["gov.in", "police.org"]:
            is_admin = True
            print("THIS USER IS ADMIN")  # Automatically mark user as admin if from an authorized domain
        else:
            is_admin = False
        try:
            print("we are in try")
            user = Users(
                name=request.form.get("name-form"),
                number_plate=request.form.get("number-plate-form").lower(),  # Convert to uppercase here
                phone_number=request.form.get("phone-number-form"),
                email=request.form.get("email-address-form"),  # Ensure car_model is also in uppercase
                emergency_contact=request.form.get("emergency-number-form"), 
                password=generate_password_hash(request.form.get("password-form")),
                is_admin=is_admin
                  # Make sure to save the password
            )
            print("name", user.name)
            print("number plate", user.number_plate)
            print("phone number", user.phone_number)
            print("email", user.email)
            print("emergency number", user.emergency_contact)
            print("car model", user.car_model)
            print("password", user.password)








            db.session.add(user)
            db.session.commit()
            print("User added successfully.")
            return redirect("/")
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            print(f"Error adding user: {e}")
            flash("There was an issue signing you up. Please try again.", "danger")
            return render_template("Sign_up.html")
    return render_template("Sign_up.html")
        # db.create_all() 




with app.app_context():
    try:
        db.create_all()
        print("Database created successfully.")
    except Exception as e:
        print(f"Error creating database: {e}")

if __name__ == '__main__':
        app.run(debug=True)



        