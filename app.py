import main as m
import flask
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import uuid
import os

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = ["jpg", "jpeg", "bmp", "png"]

'''
@app.route("/")
def welcome():
    return render_template(".html")
'''
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['POST','GET'])
def upload_file():
    # check if the post request has the file part
    if request.method == 'GET':
        return render_template("front.html")
    else:
        if 'file' not in request.files or request.files['file'].filename == '':
            return jsonify([
                {"message": "No files found"}
            ])

        file = request.files['file']
        if file and allowed_file(file.filename):
            #filename = uuid.uuid4().hex + ".png"
            #file.save(os.path.join("input", filename))
            results = m.predict(file)

            return render_template("last.html",records = results[0]["prediction"],pic = results[0]["uri"])
            '''
        return jsonify([
            {"message": "Something went wrong"}
        ])'''


if __name__ == "__main__":
    app.run()