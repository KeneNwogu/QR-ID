import os

import cloudinary
from cloudinary import uploader
import pyqrcode
from urllib.parse import urljoin, urlparse
from bson import ObjectId
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_pymongo import PyMongo
from pyzbar.pyzbar import decode
from werkzeug.utils import secure_filename

from forms import ProfileForm

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'my-test-secret-for-now'
app.config['MONGO_URI'] = os.environ.get('MONGO_URI') or 'mongodb://127.0.0.1/qr'
app.config['UPLOAD_EXTENSIONS'] = {'.jpg', '.png', '.jpeg', '.PNG', '.JPG', '.JPEG'}
app.config['UPLOAD_PATH'] = 'tmp'
app.config['DEBUG'] = os.environ.get('DEBUG') or False

mongo = PyMongo()
mongo.init_app(app)

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)


@app.route('/')
def homepage():
    form = ProfileForm()
    return render_template('index.html', form=form)


@app.route('/qr-results', methods=['POST'])
def create_qr_code():
    form = ProfileForm()
    if form.validate_on_submit():
        # create user profile
        user_info_fields = ['name', 'phone', 'email', 'website', 'address', 'job_title']
        social_fields = ['facebook', 'instagram', 'linkedin', 'twitter']
        user_data = {'social_links': {}}

        for field in user_info_fields:
            user_data[field] = getattr(form, field).data
        for field in social_fields:
            user_data['social_links'][field] = getattr(form, field, None).data

        # handle profile image separately
        profile_image = request.files.get('profile_image')
        filename = secure_filename(profile_image.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            else:
                # upload to cloudinary
                data = uploader.upload(profile_image)
                image_url = data.get('url')
                user_data['profile_image'] = image_url

        user = mongo.db.users.insert_one(user_data)
        user_id = str(user.inserted_id)
        hostname = urlparse(request.base_url).hostname
        base_url = 'https://' + hostname + '/profile'
        user_profile_link = base_url + '/' + user_id
        qr = pyqrcode.create(user_profile_link)
        qr_image = qr.png(f'static/QRs/{user_id}.png', scale=6)
        return render_template('qr-results.html', qrcode=f'{user_id}.png')
    return render_template('index.html', form=form)


@app.route('/check-qr', methods=['GET', 'POST'])
def check_qr_code():
    if request.method == "POST":
        file = request.files.get('qr')
        filename = secure_filename(file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
        file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        data = decode(Image.open(os.path.join(app.config['UPLOAD_PATH'], filename)))
        profile_link = data[0].data.decode("utf-8")
        # TODO: delete file
        return redirect(profile_link)
    return render_template('upload-qr.html')


@app.route('/profile/<user_id>')
def user_identification(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return render_template('invalid-qr.html')
    return render_template('user-details.html', user=user, qrcode=f'{str(user.get("_id"))}.png')


if __name__ == '__main__':
    app.run(debug=True)
