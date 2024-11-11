from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Mock user data with username, email, and password
users = {
    "user@example.com": {"username": "user1", "password": "password123"}
}


def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # Return an empty dictionary if the file doesn't exist yet

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()  # Load users from the JSON file
        user_email = None
        
        # Find the user by username (not email)
        for email, user_info in users.items():
            if user_info['username'] == username and user_info['password'] == password:
                user_email = email
                break
        
        if user_email:
            session['user'] = users[user_email]['username']  # Store username in session
            flash('Login successful!', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        users = load_users()  # Load users from the JSON file
        
        # Ensure the email and username don't already exist
        if email not in users and all(user['username'] != username for user in users.values()):
            users[email] = {"username": username, "password": password}  # Add new user to the dictionary
            save_users(users)  # Save updated users to the JSON file
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email or username already exists. Please login.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('signup.html')


# Load data
def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

# Save data
def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def homepage():
    data = load_data()
    posts = data.get("posts", [])
    
    # Get the current logged-in user's username (if any)
    username = session.get('user', None)  # Default to None if not logged in
    
    return render_template('index.html', posts=posts, username=username)

@app.route('/get_usernames')
def get_usernames():
    with open('users.json', 'r') as f:
        data = json.load(f)
    usernames = [user_info['username'] for user_info in data.values()]
    return jsonify(usernames)


@app.route('/mypage')
def my_page():
    # Ensure user is logged in
    if 'user' not in session:
        flash('Please login to access your page.', 'danger')
        return redirect(url_for('login'))

    # Filter posts by user
    user_email = session['user']
    data = load_data()
    user_posts = [post for post in data['posts'] if post['author'] == user_email]
    
    return render_template('mypage.html', posts=user_posts)



@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    data = load_data()
    comment = request.form["comment"]
    for post in data["posts"]:
        if post["id"] == post_id:
            post["comments"].append({"text": comment, "replies": []})
            break
    save_data(data)
    return redirect(f'/post/{post_id}')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    data = load_data()
    # Simple search by title or description
    filtered_posts = [post for post in data['posts'] if query.lower() in post['title'].lower() or query.lower() in post['description'].lower()]
    return render_template('index.html', posts=filtered_posts)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.pop('user', None)
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))
    return redirect(url_for('home'))  # Optional: Add a fallback for GET requests.

# Load data
def load_data():
    with open('data.json', 'r') as f:
        return json.load(f)

# Save data
def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/upvote/<int:post_id>', methods=['POST'])
def upvote(post_id):
    data = load_data()
    
    # Find the post by id
    post = next((p for p in data['posts'] if p['id'] == post_id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    
    # Initialize upvotes and downvotes if not present
    if 'upvotes' not in post:
        post['upvotes'] = 0
    if 'downvotes' not in post:
        post['downvotes'] = 0
    
    # Increment the upvotes
    post['upvotes'] += 1
    
    # Save the updated data
    save_data(data)
    
    return jsonify({"upvotes": post['upvotes'], "downvotes": post['downvotes']})


@app.route('/downvote/<int:post_id>', methods=['POST'])
def downvote(post_id):
    data = load_data()
    
    # Find the post by id
    post = next((p for p in data['posts'] if p['id'] == post_id), None)
    if post is None:
        return jsonify({"error": "Post not found"}), 404
    
    # Initialize upvotes and downvotes if not present
    if 'upvotes' not in post:
        post['upvotes'] = 0
    if 'downvotes' not in post:
        post['downvotes'] = 0
    
    # Increment the downvotes
    post['downvotes'] += 1
    
    # Save the updated data
    save_data(data)
    
    return jsonify({"upvotes": post['upvotes'], "downvotes": post['downvotes']})



@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user' not in session:
        flash('Please login to create a post.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        
        # Generate new post data
        new_post = {
            "id": len(load_data()["posts"]) + 1,  # Auto-incrementing ID
            "title": title,
            "description": description,
            "link": link,
            "upvotes": 0,
            "downvotes": 0,
            "comments": [],
            "author": session['user']
        }
        
        # Load existing posts and append the new post
        data = load_data()
        data["posts"].append(new_post)
        save_data(data)
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('my_page'))

    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    data = load_data()
    post = next((p for p in data.get("posts", []) if p["id"] == post_id), None)
    return render_template('post.html', post=post) if post else "Post not found", 404


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Check if the user has dark mode preference saved in session/local storage
    dark_mode = False
    if 'dark_mode' in session:
        dark_mode = session['dark_mode']  # Set dark_mode based on session

    return render_template('settings.html', dark_mode=dark_mode)


# In your app.py, when handling the dark mode toggle
@app.route('/toggle_dark_mode', methods=['POST'])
def toggle_dark_mode():
    if 'dark_mode' not in session:
        session['dark_mode'] = False  # Default to False (light mode)
    
    # Toggle the dark_mode session variable
    session['dark_mode'] = not session['dark_mode']
    
    return redirect(url_for('settings'))

@app.route('/developer')
def developer():
    return render_template('developer.html')


# Directory where chat files will be stored
CHAT_DIR = 'chats/'

if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

import json

@app.route('/chat')
def chat():
    current_user = session.get('user')  # Get the current logged-in user
    existing_chats = []
    all_users = []

    # List all chat files involving the current user
    for filename in os.listdir(CHAT_DIR):
        if filename.endswith(".txt"):
            users = filename[:-4].split("_")
            if current_user in users:
                other_user = users[0] if users[1] == current_user else users[1]
                existing_chats.append(other_user)

    # Load all usernames from users.json
    with open('users.json', 'r') as file:
        users_data = json.load(file)
        all_users = [user_info['username'] for email, user_info in users_data.items() if user_info['username'] != current_user]

    return render_template('chat.html', existing_chats=existing_chats, all_users=all_users)



@app.route('/chat/messages/<user>', methods=['GET'])
def get_messages(user):
    current_user = session.get('user')  # Get the logged-in user from the session
    if not current_user:
        return jsonify({'error': 'User not logged in'}), 403

    chat_file = get_chat_file(current_user, user)

    # Load the messages from the chat file
    if os.path.exists(chat_file):
        with open(chat_file, 'r') as file:
            messages = json.load(file)
    else:
        messages = []

    return jsonify(messages)

@app.route('/chat/send/<user>', methods=['POST'])
def send_message(user):
    current_user = session.get('user')  # Get the logged-in user from the session
    if not current_user:
        return jsonify({'error': 'User not logged in'}), 403

    data = request.get_json()
    message_text = data['message']

    chat_file = get_chat_file(current_user, user)
    if os.path.exists(chat_file):
        with open(chat_file, 'r') as file:
            messages = json.load(file)
    else:
        messages = []

    new_message = {
        'sender': current_user,
        'text': message_text
    }

    messages.append(new_message)

    # Save the updated messages to the chat file
    with open(chat_file, 'w') as file:
        json.dump(messages, file, indent=4)

    return jsonify({"status": "success", "message": new_message})

def get_chat_file(user1, user2):
    # Sort the usernames alphabetically to ensure the file name is consistent
    users = sorted([user1, user2])
    # Generate a unique chat file for the pair of users
    return os.path.join(CHAT_DIR, f"{users[0]}_{users[1]}.txt")


# Main entry point
if __name__ == '__main__':
    app.run(debug=True)

