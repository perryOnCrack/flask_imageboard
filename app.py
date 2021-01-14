from flask import Flask, jsonify, render_template, flash, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import json, db, os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './images'
app.debug = True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

'''
Home page.
'''
@app.route('/', methods = ['GET'])
def index():
    data = db.get_index_data()
    if data[0]:
        return render_template('home.html', data=data[1])
    else:
        return render_template('error.html', error=data[1])

'''
A board (thread list.)
'''
@app.route('/<b_id>/<page>', methods = ['GET'])
def board(b_id, page):
    page = page[1:]
    data = db.get_board_data(b_id, page)
    if data[0]:
        return render_template('board.html', b_id=b_id, data=data[1])
    else:
        return render_template('error.html', error=data[1])

'''
A thead (comment list.)
'''
@app.route('/<b_id>/<t_id>/all', methods = ['GET'])
def thread(b_id, t_id):
    data = db.get_thread_data(b_id, t_id)
    if data[0]:
        return render_template('thread.html', b_id=b_id, t_id=t_id, data=data[1])
    else:
        return render_template('error.html', error=data[1])

'''
Create comment.
'''
@app.route('/<b_id>/<t_id>/comment', methods = ['POST'])
def comment(b_id, t_id):
    filename = None
    if 'img' in request.files:
        file = request.files['img']
        # if user does not select file, browser also submit an empty part without filename
        if (file.filename != '') and (file and allowed_file(file.filename)):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    result = db.set_comment(b_id, t_id, comment=request.form.get('comment'), image=filename)
    print(result)
    if result[0]:
        return redirect(f'/{b_id}/{result[1]}/all')
    else:
        return render_template('error.html', error=result[1])

'''
Serve images.
'''
@app.route('/images/<fname>', methods = ['GET'])
def image(fname):
    return send_from_directory('images', fname)


if __name__ == '__main__':
    app.run()
