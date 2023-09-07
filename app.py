from flask import Flask, request, jsonify, make_response,session
from pymongo import MongoClient
from datetime import datetime
import bcrypt
from email_validator import validate_email, EmailNotValidError

from note import Note
import openai
from pymongo.server_api import ServerApi


app = Flask(__name__)

# Connect MongoDb Client

uri = "use your URI for mongodb or use localhost client below"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

#client = MongoClient('mongodb://localhost:27017')
db = client['registered_users']
collection = db['login_data']
notes_collection = db['notes']


@app.route('/genrateaisumdum/<text>',methods=['GET','OPTIONS'])
def generateaisudum(text):
    print(text)
    openai.api_key = "Your API KEY"

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": text
        }
    ],
    temperature=0,
    max_tokens=1024,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()
    
    return (_corsify_actual_response(jsonify(response)))

@app.route('/genrateaisum/',methods=['GET'])
def generateaisum():
    # openai.api_key = "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"
    mytext = "I am learning about thermodynamics."
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": mytext
        }
    ],
    temperature=0,
    max_tokens=1024,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    return (jsonify(response))

# create new note 
# TODO Option to make it private, field need
@app.route('/notes', methods=['POST'])
def create_note():

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    content_dict = dict()
    tags = data.get('tags')
    created_by_user_id = data.get('username')
    # user_note = []
    # user_note.append(User_note(created_by_user_id, content))
    content_dict[created_by_user_id] = content

    if not title :
        return jsonify({'message': 'Please provide title'}), 400

    note = Note(title+created_by_user_id, title, created_by_user_id, tags, content_dict, datetime.now())

    result = notes_collection.insert_one(note.__dict__)
    return jsonify({'message': 'Note created successfully',
                     'username' : created_by_user_id,
                      'success' : True }), 201

# edit note with note id
@app.route('/updatenote/<note_id>', methods=['POST','OPTIONS'])
def update_note(note_id):

    print("inside /updatenote/<note_id>")
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()
    
    data = request.get_json()
    content = data.get('content')
    updated_by_user = data.get('updated_by_user')

    if not content:
        return _corsify_actual_response(jsonify({'message': 'Please provide both title and content'})), 400
    print(note_id)
    # Check if the note with the given ID exists and belongs to the logged-in user
    existing_note = notes_collection.find_one({'note_id': note_id})
    if not existing_note:
        return _corsify_actual_response(jsonify({'message': 'Note not found or unauthorized to update'})), 404
    new_content = existing_note.get('content')
    print(new_content)
    new_content[updated_by_user] = content
    
    
    updated_note = Note(existing_note.get('note_id'), existing_note.get('title'), existing_note.get('created_by_user_id') , existing_note.get('tags'), new_content,existing_note.get('create_date'))

    notes_collection.update_one({'note_id': note_id}, {'$set': updated_note.__dict__})

    return _corsify_actual_response(jsonify({'message': 'Note updated successfully',
                    'success': 'true'})), 200

# update note comment with note id
@app.route('/updatenotecomment/<note_id>', methods=['POST','OPTIONS'])
def update_note_comment(note_id):

    print("inside /updatenotecomment/<note_id>")
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()
    
    data = request.get_json()
    content = data.get('content')
    updated_by_user = data.get('updated_by_user')

    if not content:
        return _corsify_actual_response(jsonify({'message': 'Please provide both title and content'})), 400
    print(note_id)
    # Check if the note with the given ID exists and belongs to the logged-in user
    existing_note = notes_collection.find_one({'note_id': note_id})
    if not existing_note:
        return _corsify_actual_response(jsonify({'message': 'Note not found or unauthorized to update'})), 404
    new_content = existing_note.get('content')
    print(new_content)
    new_content[updated_by_user+"-comment"] = content
    
    
    updated_note = Note(existing_note.get('note_id'), existing_note.get('title'), existing_note.get('created_by_user_id') , existing_note.get('tags'), new_content,existing_note.get('create_date'))

    notes_collection.update_one({'note_id': note_id}, {'$set': updated_note.__dict__})

    return _corsify_actual_response(jsonify({'message': 'Comment on the note updated successfully',
                    'success': 'true'})), 200

# Get all notes in the system
@app.route('/getnotes', methods=['GET','OPTIONS'])
def get_notes():
    print("inside get notes")
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()

   # Get notes with the specified tag belonging to the logged-in user  
    notes_details = notes_collection.find()
    result_notes =[]
    for note in notes_details:
        current_note_object = to_note_object(note)
        result_notes.append(current_note_object)

    return_notes=[note.__dict__ for note in result_notes]
    if not notes_details:
        return jsonify({'message': 'No notes found with the specified tag'}), 404

    return _corsify_actual_response(jsonify({'notes': return_notes}))

# register new user with username and email 
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password') 

# Check if either username or email is provided
    if not username or not email:
        return jsonify({'message': 'Please provide either username or email.'}), 400
    
# verify email address
    if is_valid_email(email):
        print("Valid email address. Move on for next validation")
    else:
       return jsonify({'message': 'Please provide valid email.'}), 400
    
    user = collection.find_one({'$or':[{'username':username},{'email':email}]})
 
 # Verify the password
    if user:
        return jsonify({'message': 'username or email already exists.'}), 409
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    

    new_user = {
        'user_id':username,
        'username':username,
        'email' : email,
        'password': hashed_password   
    }
    collection.insert_one(new_user)
    return jsonify({'message':'User registered successfully',
                    'username': username,
                    "success": "true",
                    }),201


# login with username and password
@app.route('/login', methods=['POST'])

def login():
    data = request.get_json()
    username = data.get('username')
    #email = data.get('email')
    password = data.get('password')
    print("Input User " + username)

# Check if either username or email is provided
    if not username:
        return jsonify({'message': 'Please provide either username or email.'}), 400

    # Find the user in the database based on username or email
    query = {}
    query['user_id'] = username
    print(query)
    print("Password "+password)
    user = collection.find_one(query)
    print(user)
    
    inputbytes = password.encode('utf-8')
    
 # Verify the password
    if bcrypt.checkpw(inputbytes, user["password"]):
        return jsonify({'message': 'Login successful',
                    'success': 'true',
                    'username': user["username"]}), 200
        
    else:
        return jsonify({'message': 'Invalid Credentials'}), 404
  

# filter notes on note_id
@app.route('/notes/bynoteid/<note_id>', methods=['GET','OPTIONS'])
def get_notes_by_note_id(note_id):
    print(request)
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()
               
    # Get notes belonging to the logged-in user
    query = {} 
    query['note_id'] = note_id
    print(notes_collection.find_one(query))
    notes_by_content_note = to_note_object(notes_collection.find_one(query))
    print("Data From notes")
    print(notes_by_content_note)
    
    if not notes_by_content_note:
        return jsonify({'message': 'Notes not found for the specified user_id'}), 404

    return _corsify_actual_response(jsonify( notes_by_content_note.__dict__))


# filter notes on user_id
@app.route('/notes/<user_id>', methods=['GET','OPTIONS'])
def get_notes_by_user(user_id):
    
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()
               
    # Get notes belonging to the logged-in user

    result_notes = []

    notes_by_content_user = notes_collection.find()
    print("Data From notes")
    print(notes_by_content_user)
    for note in notes_by_content_user:
        current_note_object = to_note_object(note)
        if current_note_object.created_by_user_id == user_id or user_id in current_note_object.content:
            print(current_note_object.content[user_id])
            print(current_note_object.created_by_user_id == user_id)
            result_notes.append(current_note_object)
        

    if not notes_by_content_user:
        return jsonify({'message': 'Notes not found for the specified user_id'}), 404

    return_notes=[note.__dict__ for note in result_notes]
    return _corsify_actual_response(jsonify({'notes': return_notes})) 

#Logout    
@app.route('/logout', methods=['POST'])
def logout():
    # Perform logout logic here (e.g., clear session, revoke tokens, etc.).
    
    session.clear()
    # Return a success message or status code.
    response = make_response(jsonify({'message': 'Logged out successfully'}))
    response.set_cookie('user_token', '', expires=0)
    return response

# search note
@app.route('/search/<note_id>', methods=['GET','OPTIONS'])
def search_notes(note_id):
    print("inside search notes")
    if request.method == "OPTIONS": # CORS preflight
        print(request)
        return _build_cors_preflight_response()

   # Get notes with the specified tag belonging to the logged-in user  
    notes_details = notes_collection.find()
    result_notes =[]
    for note in notes_details:
        current_note_object = to_note_object(note)
        print("Tag = "+current_note_object.tags)
        print("title = "+current_note_object.title)
        if note_id.lower() in current_note_object.tags.lower()  or note_id.lower() in current_note_object.title.lower() : 
        # if  current_note_object.tags.find(note_id)  or current_note_object.title.find(note_id) : 
            result_notes.append(current_note_object)

    return_notes=[note.__dict__ for note in result_notes]
    print(return_notes)
    print(len(return_notes))
    if len(return_notes) == 0:
        return _corsify_actual_response(jsonify({'message': 'No notes found with the specified tag'}))

    return _corsify_actual_response(jsonify({'notes': return_notes,
                                             'success': 'true'}))


def is_valid_email(email):
        try:
            valid = validate_email(email)
            return True
        except EmailNotValidError:
            return False

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def authenticate_password(input_password, stored_password):
    salt = stored_password[:29]
    print("salt password is :", salt)
    stored_hashed_password = stored_password[29:]
    print("stored hassed", stored_hashed_password)
    userBytes = input_password.encode('utf-8')
    print("userBytes is :", userBytes)
    encoded_attempt= bcrypt.checkpw(userBytes, stored_hashed_password)
    print("encoded_attempt",encoded_attempt )
    return encoded_attempt

    #if encoded_attempt:
    #bcrypt.checkpw(encoded_attempt, stored_password):
        #print("Matched")
       # return True
    #else:
      #  print("Not Matched")
      #  return False
    

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def to_note_object(note):
    return Note(note.get('note_id'), note.get('title'), note.get('created_by_user_id') , note.get('tags'), note.get('content'),note.get('create_date'))


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

# if __name__ == '__main__':
#     app.run(debug=True)
