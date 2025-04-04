import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
from datetime import datetime
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)

stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stdout_handler.setFormatter(formatter)
stderr_handler.setFormatter(formatter)

logger.handlers = [stdout_handler, stderr_handler]


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

@app.route('/healthz')
def isHealthy():
    try:
        connection = get_db_connection()
        table_check_query = '''
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='posts'
        '''
        table = connection.execute(table_check_query).fetchone()
        if not table:
            raise sqlite3.Error("Table 'posts' does not exist")

        # Check if the necessary fields exist in the 'posts' table
        column_check_query = '''
        PRAGMA table_info(posts)
        '''
        columns = connection.execute(column_check_query).fetchall()
        required_columns = {'id', 'created', 'title', 'content'}
        existing_columns = {column['name'] for column in columns}

        if not required_columns.issubset(existing_columns):
            raise sqlite3.Error("Table 'posts' does not have the required fields")
        connection.close()
        response = {
            "result": "OK - healthy"
        }
        return jsonify(response), 200
    except sqlite3.Error:
        response = {
            "result": "ERROR - database not ready"
        }
        return jsonify(response), 500


# Track the number of database connections
db_connection_count = 0

@app.route('/metrics')
def get_metrics():
    global db_connection_count
    try:
        connection = get_db_connection()
        post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        connection.close()
        response = {
            "db_connection_count": db_connection_count,
            "post_count": post_count
        }
        return jsonify(response), 200
    except sqlite3.Error:
        response = {
            "error": "Unable to fetch metrics"
        }
        return jsonify(response), 500

# Override the get_db_connection function to track connections
def get_db_connection():
    global db_connection_count
    db_connection_count += 1
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logging.error(f'{datetime.now()}, Article with ID {post_id} does not exist. Returning 404.')
        return render_template('404.html'), 404
    else:
        logging.info(f'{datetime.now()}, Article "{post["title"]}" retrieved!')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info(f'{datetime.now()}, "About Us" page retrieved!')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logging.info(f'{datetime.now()}, New article "{title}" created!')
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
