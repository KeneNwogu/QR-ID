import os
import pyqrcode
from bson import ObjectId
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for
from flask_pymongo import PyMongo
from pyzbar.pyzbar import decode
from werkzeug.utils import secure_filename

from forms import ProfileForm

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'my-test-secret-for-now'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI') or 'mongodb://127.0.0.1/qr'
app.config['UPLOAD_PATH'] = 'tmp'
app.config['DEBUG'] = os.environ.get('DEBUG') or False

mongo = PyMongo()
mongo.init_app(app)


@app.route('/')
def homepage():
    form = ProfileForm()
    return render_template('index.html', form=form)


@app.route('/qr-results', methods=['POST'])
def create_qr_code():
    form = ProfileForm()
    if form.validate_on_submit():
        # create user profile
        user_info_fields = ['name', 'phone', 'email', 'website']
        social_fields = ['facebook', 'instagram', 'linkedin', 'twitter']
        user_data = {'social_links': {}}

        for field in user_info_fields:
            user_data[field] = getattr(form, field).data
        for field in social_fields:
            user_data['social_links'][field] = getattr(form, field, None).data

        user = mongo.db.users.insert_one(user_data)
        user_id = str(user.inserted_id)
        qr = pyqrcode.create(user_id)
        qr_image = qr.png(f'static/QRs/{user_id}.png', scale=6)
        return render_template('qr-results.html', qrcode=f'{user_id}.png')


@app.route('/check-qr', methods=['GET', 'POST'])
def check_qr_code():
    if request.method == "POST":
        file = request.files.get('qr')
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        data = decode(Image.open(os.path.join(app.config['UPLOAD_PATH'], filename)))
        user_id = data[0].data.decode("utf-8")
        # TODO: delete file
        return redirect(url_for('user_identification', user_id=user_id))
    return render_template('upload-qr.html')


@app.route('/profile/<user_id>')
def user_identification(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return render_template('invalid-qr.html')
    return render_template('user-details.html', user=user, qrcode=f'{str(user.get("_id"))}.png')


if __name__ == '__main__':
    app.run(debug=True)