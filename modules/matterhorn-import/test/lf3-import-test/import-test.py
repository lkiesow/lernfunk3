import time
from flask import Flask, request
from functools import wraps
from werkzeug.contrib import authdigest
app = Flask(__name__)

class FlaskRealmDigestDB(authdigest.RealmDigestDB):
	def requires_auth(self, f):
		@wraps(f)
		def decorated(*args, **kwargs):
			if not self.isAuthenticated(request):
				return self.challenge()
			return f(*args, **kwargs)

		return decorated

authDB = FlaskRealmDigestDB('MyAuthRealm')
authDB.add_user('mh2lf', 'secret')

@app.route("/")
@authDB.requires_auth
def hello():
	return "Hello World!\n"


@app.route('/', methods=['PUT','POST'])
@authDB.requires_auth
def get_data():
	mpkg = request.form.get('mediapackage')
	if not mpkg:
		return 'No mediapackage attached\n', 400

	try:
		f = open('./mediapackages/%s.xml' % time.time(), 'w')
		f.write( mpkg )
	except StandardError:
		return 'Could not write mediapackage\n', 500
	finally:
		f.close()

	return 'Mediapackage received\n'


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0')
