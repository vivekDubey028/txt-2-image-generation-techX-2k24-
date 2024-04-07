from flask import Flask, request, redirect, jsonify, session, render_template,url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime
from flask_allowedhosts import limit_hosts

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Set a secret key for the session
app.config['DEBUG'] = False  # Disable the Flask debugger

# Database connection parameters
DB_HOST = "localhost"
DB_NAME = "chatgpt"
DB_USER = "postgres"
DB_PASS = "ezwq2173"

# Establish a database connection
def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

# Function to create database tables
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            fullname VARCHAR(100),
            email VARCHAR(100),
            collegename VARCHAR(100),
            phonenumber VARCHAR(15),
            lab VARCHAR(50)
            )
    """)

    # Create submissions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id),
            submission_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prompt_text varchar,
            image_url VARCHAR(255),
            final_submission BOOLEAN DEFAULT FALSE
        )
    """)
    cur.execute("""
            CREATE TABLE IF NOT EXISTS vote (
        vote_id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(user_id),
        submission_id INTEGER REFERENCES submissions(submission_id),
        image_url VARCHAR(255),
        vote INTEGER -- Adding the new vote column
            )
                """)

    conn.commit()
    cur.close()
    conn.close()

# Call the function to create tables
create_tables()

# Define the API endpoint for image generation
IMAGE_GENERATION_API = "https://modelslab.com/api/v6/realtime/text2img"
# Replace this with your actual bearer token

ALLOWED_HOSTS = ['10.1.15.2', '10.1.15.3', '10.1.15.4', '10.1.15.5', '10.1.15.6', '10.1.15.7',
    '10.1.15.8', '10.1.15.9', '10.1.15.10', '10.1.15.11', '10.1.15.12', '10.1.15.13',
    '10.1.15.14', '10.1.15.15', '10.1.15.16', '10.1.15.17', '10.1.15.18', '10.1.15.19',
    '10.1.15.20', '10.1.15.21', '10.1.15.22', '10.1.15.23', '10.1.15.24', '10.1.18.1',
    '10.1.18.2', '10.1.18.3', '10.1.18.4', '10.1.28.26', '10.1.18.6', '10.1.18.7',
    '10.1.18.8', '10.1.18.9', '10.1.18.10', '10.1.18.11', '10.1.18.12', '10.1.18.13',
    '10.1.18.14', '10.1.18.15', '10.1.28.34', '10.1.18.17', '10.1.18.19', '10.1.18.20',
    '10.1.18.21', '10.1.26.77', '10.1.18.23', '10.1.18.24','127.0.0.1']
# Define your login route
@app.route('/', methods=['GET', 'POST'])
@limit_hosts(ALLOWED_HOSTS)
def index():
    if request.method == 'POST':
        try:
            data = request.form
            username = data['username']
            email = data['email']
            full_name = data['fullname']
            phone_number = data['phonenumber']
            college_name = data['collegename']
            lab = data['lab']

            # Store username in session
            session['username'] = username

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('INSERT INTO users (username, email, lab, fullname, phonenumber, collegename) VALUES (%s, %s, %s, %s, %s, %s)',
                        (username, email, lab, full_name, phone_number, college_name))
            conn.commit()
            cur.close()
            conn.close()

            # Redirect to the image generation page after successful login
            return redirect('/generate_image')

        except KeyError as e:
            # Missing required field in form data
            error_message = f"Missing required field: {str(e)}"
            return render_template('error.html', status='error', message=error_message), 400

        except psycopg2.IntegrityError as e:
            # Database constraint violation (e.g., duplicate key)
            error_message = "The given Information has already been recorderd. Please try again with new Details!."
            return render_template('error.html', status='error', message=error_message), 500

        except Exception as e:
            # Other unexpected errors
            error_message = "An unexpected error occurred. Please contact Volunteers!."
            return render_template('error.html', status='error', message=error_message), 500

    else:
        return render_template('index.html')


# Define your login route
@app.route('/login', methods=['GET', 'POST'])
@limit_hosts(ALLOWED_HOSTS)
def login():
    if request.method == 'POST':
        try:
            data = request.form
            username = data['username']
            phone_number = data['phonenumber']

            # Check if the username and phone number exist in the database
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute('SELECT * FROM users WHERE username = %s AND phonenumber = %s', (username, phone_number))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user:
                # Store username in session
                session['username'] = user['username']
                return redirect('/generate_image')  # Redirect to the image generation page after successful login
            else:
                error_message = "Invalid username or phone number"
                return render_template('login.html', error=error_message)

            # Redirect to the image generation page after successful login
            return redirect('/generate_image')

        except Exception as e:
            error_message = "An error occurred: " + str(e)
            return render_template('login.html', error=error_message)

    else:
        return render_template('login.html')

# Define the image generation route
@app.route('/generate_image', methods=['GET', 'POST'])
@limit_hosts(ALLOWED_HOSTS)
def generate_image():
    if request.method == 'POST':
        data = request.json

        # Prepare data for the API call
        payload = {
            "key": "bK7OnLhSufswiXktBY38IDbPP4TlzJSAiPcW9GyLHtilcngZoVE8zAGYpips",
            "prompt": data.get('prompt', ''),
            "negative_prompt": data.get('negative_prompt', ''),
            "width": data.get('width', ''),
            "height": data.get('height', ''),
            "providers": data.get('providers', ''),  # Handle the case where 'providers' might not exist
            "fallback_providers": data.get('fallback_providers', ''),
            "safety_checker": True,  # Make safety_checker static
            "guidance_scale": 7.5,
        }

        # Set up headers with the bearer token
        headers = {
            'Content-Type': 'application/json'
        }

        # Make a request to the image generation API
        response = requests.post(IMAGE_GENERATION_API, json=payload, headers=headers)
        response_data = response.json()

        # Check if image generation was successful
        if response_data.get('status') == 'success' and 'output' in response_data:
            generated_image_url = response_data['output'][0]  # Assuming the first URL in 'output' list is the generated image URL

            # Fetch user ID from the session or database
            if 'user_id' in session:
                user_id = session['user_id']
            else:
                # If user ID is not found in session, fetch it from the database using username
                username = session['username']  # Assuming you store username in the session
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('SELECT user_id FROM users WHERE username = %s', (username,))
                    user = cur.fetchone()
                    if user:
                        user_id = user[0]
                    else:
                        # Handle case where user is not found
                        return jsonify({'status': 'error', 'message': 'User not found'}), 404
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 500
                finally:
                    cur.close()
                    conn.close()

            # Store the generated image in the database
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('INSERT INTO submissions (user_id, prompt_text, image_url, submission_datetime, final_submission) VALUES (%s, %s, %s, %s, %s)',
                            (user_id, data.get('prompt', ''), generated_image_url, datetime.now(), False))
                conn.commit()
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
            finally:
                cur.close()
                conn.close()

            # Return the response from the image generation API
            return jsonify({'status': 'success', 'image_url': generated_image_url})

        else:
            return jsonify({'status': 'error', 'message': 'Image generation failed'})

    elif request.method == 'GET':
        if 'username' in session:
            username = session['username']
            try:
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute('SELECT image_url FROM submissions JOIN users ON submissions.user_id = users.user_id WHERE username = %s ORDER BY submission_datetime DESC', (username,))
                data = cur.fetchall()
                cur.close()
                conn.close()
                return render_template('generate_image.html', users=data)
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

    else:
        return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405




# Define the route to fetch the generated image URL from the database
@app.route('/get_generated_image', methods=['GET'])
def get_generated_image():
    if 'username' in session:
        username = session['username']
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT image_url FROM submissions JOIN users ON submissions.user_id = users.user_id WHERE username = %s ORDER BY submission_datetime DESC', (username,))
            result = cur.fetchall()
            if result:
                return jsonify({'status': 'success', 'image_url': result[0]})
            else:
                return jsonify({'status': 'error', 'message': 'Image URL not found'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
        finally:
            cur.close()
            conn.close()
    else:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401



# Define the route to submit the selected image to the database
@app.before_request
def before_request():
    if request.path == '/lab1' and 'username' in session:
        username = session['username']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT lab FROM users WHERE username = %s', (username,))
        user_lab = cur.fetchone()
        cur.close()
        conn.close()
        if user_lab and user_lab[0] == 'lab1':
            return redirect('/lab2')
    elif request.path == '/lab2' and 'username' in session:
        username = session['username']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT lab FROM users WHERE username = %s', (username,))
        user_lab = cur.fetchone()
        cur.close()
        conn.close()
        if user_lab and user_lab[0] == 'lab2':
            return redirect('/lab1')

@app.route('/submit_image', methods=['POST'])
def submit_image():
    selected_image_url = request.form.get('selectedImageUrl')

    if selected_image_url:
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Update the final_submission column to True for the submitted image URL
            cur.execute('UPDATE submissions SET final_submission = TRUE WHERE image_url = %s', (selected_image_url,))
            conn.commit()

            # Insert selected image data into the vote table
            cur.execute("""
                INSERT INTO vote (image_url, user_id, submission_id)
                SELECT image_url, user_id, submission_id
                FROM submissions
                WHERE final_submission = TRUE AND image_url = %s
            """, (selected_image_url,))
            conn.commit()

            cur.close()
            conn.close()

            # Redirect to the appropriate lab page based on user's lab
            if 'username' in session:
                username = session['username']
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('SELECT lab FROM users WHERE username = %s', (username,))
                user_lab = cur.fetchone()
                if user_lab and user_lab[0] == 'lab1':
                    return redirect('/lab2')  # Redirect users from lab 1 to lab 2
                elif user_lab and user_lab[0] == 'lab2':
                    return redirect('/lab1')  # Redirect users from lab 2 to lab 1
                else:
                    # Handle case where user's lab is not defined or unknown
                    return jsonify({'status': 'error', 'message': 'User lab not defined or unknown'}), 400
            else:
                # Handle case where user is not logged in
                return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    else:
        return jsonify({'status': 'error', 'message': 'No image selected'})

    
# Route to render lab1.html template
@app.route('/lab1', methods=['GET'])
def lab1():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT s.image_url, s.prompt_text FROM submissions s JOIN users u ON s.user_id = u.user_id WHERE u.lab = 'lab1' AND s.final_submission = true")
        data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('lab1.html', users=data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Route to render lab2.html template
@app.route('/lab2', methods=['GET'])
def lab2():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT s.image_url, s.prompt_text FROM submissions s JOIN users u ON s.user_id = u.user_id WHERE u.lab = 'lab2' AND s.final_submission = true")
        data = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('lab2.html', users=data)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/submit_votes', methods=['POST'])
def submit_votes():
    if 'username' in session:
        selected_images = request.json.get('votes')
        if len(selected_images) != 3:
            return jsonify({'status': 'error', 'message': 'Please select exactly 3 images to vote.'}), 400
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            for image_url in selected_images:
                cur.execute('UPDATE vote SET vote = COALESCE(vote, 0) + 1 WHERE image_url = %s', (image_url,))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('redirect_page'))  # Redirect to the desired page
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    else:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401

@app.route('/redirect_page')
def redirect_page():
    # Render your redirect page or return a response as needed
    return render_template('redirect.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
