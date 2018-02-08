import os
from flask import Flask, request, redirect, url_for
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import apt_inst
from debian import deb822

# //TODO optimize some of the multiple connections with the database because of function calls
UPLOAD_FOLDER = './uploads/'
ALLOWED_EXTENSIONS = set(['deb'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MONGO_DBNAME'] = 'repo-project'
app.config['MONGO_URI'] = 'mongodb://172.19.4.177:27018/repo-project'

mongo = PyMongo(app)

#function to extract the info of uploaded package
def extract_info(filepath):
    package_dict = dict()
    control_data = apt_inst.DebFile(filepath).control.extractdata('control')
    control_dict = deb822.Deb822(control_data.split("\n"))
    d = dict()
    d['Version'] = str(control_dict['Version'])
    d['Architecture'] = str(control_dict['Architecture'])
    d['Maintainer'] = str(control_dict['Maintainer'])
    d['Description'] = str(control_dict['Description'])
    package_dict["data"] = list()
    package_dict["data"].append(d)
    package_dict["name"] = str(control_dict['Package'])
    return package_dict

def isexist(package_name):
    packages = mongo.db.packages
    existing_package = packages.find_one({'name' : package_name})
    if existing_package is not None:
        return True
    return False

def insert_package_in_db(package_data):
    package = mongo.db.packages
    package.insert(package_data)

#return false, if the two documents contain same data
def if_same_data(new_package_dict):
    packages = mongo.db.packages
    existing_package = packages.find_one({'name' : new_package_dict['name']})
    if existing_package is not None: #redundant check, but still :P
        if(new_package_dict['data'][0] in existing_package['data']):
            return True
    return False

def update_package_details(new_package_dict):
    packages = mongo.db.packages
    existing_package = packages.find_one({'name' : new_package_dict['name']})
    if existing_package is not None: #redundant check, but still :P
        data = existing_package['data']
        data.append(new_package_dict['data'][0])
        packages.update_one({
        '_id' : existing_package['_id']
        },{
        '$set' : {"data" : data}
        },upsert=False)
        print "I am here"



def allowed_file(filename):
    return '.' in filename and \
    filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if filename in os.listdir(app.config['UPLOAD_FOLDER']):
                return "file with same name already exist"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            new_package_dict = extract_info(filepath)
            if isexist(new_package_dict['name']):
                if if_same_data(new_package_dict):
                    return "This package already exist"
                else:
                    update_package_details(new_package_dict)
                    os.remove(filepath)
                    return "Existing package!! details updated successfully"
            insert_package_in_db(extract_info(filepath))
            # print os.path.join(app.config['UPLOAD_FOLDER'], filename)

            return redirect(url_for('index'))
    return """
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    <p>%s</p>
    """ % "<br>".join(os.listdir(app.config['UPLOAD_FOLDER'],))

@app.route('/find/<string:package_name>', methods=['GET','POST'])
def find(package_name):
    packages = mongo.db.packages
    existing_package = packages.find_one({'name' : package_name})
    if existing_package is not None:
        return str(existing_package["data"])
    return package_name + " does not exist"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
