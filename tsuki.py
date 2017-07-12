#!/usr/bin/python

import os
import re
import subprocess
import uuid

from flask import *
app = Flask(__name__)

file_list = dict()

def get_movie_duration(path):
	result = subprocess.Popen(["ffprobe", path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
	for line in result.stdout.readlines():
		match = re.search("Duration: (\d\d):(\d\d):(\d\d)", line)
		if match:
			return (int(match.group(1)) * 3600) + (int(match.group(2)) * 60) + (int(match.group(3)))
	return 0

def generate_file_list(directory):
	for filename in os.listdir(directory):
		path = os.path.join(directory, filename)
		if path.endswith(".mp4") or path.endswith(".mkv"):
			file_data = {"duration" : get_movie_duration(path),
				"fileSize" : os.path.getsize(path),
				"localPath" : path,
				"mimeType" : 'video/x-matroska' if path.endswith(".mkv") else 'video/mp4'}
			print "Adding: %s, %d seconds, %d bytes" % (filename, file_data["duration"], file_data["fileSize"])
			file_list[filename] = file_data

def send_file_partial(path, mimetype):
	range_header = request.headers.get('Range', None)
	if not range_header:
		return send_file(path, mimetype=mimetype)
	
	size = os.path.getsize(path)	
	byte1, byte2 = 0, None
	
	m = re.search('(\d+)-(\d*)', range_header)
	g = m.groups()
	
	if g[0]: byte1 = int(g[0])
	if g[1]: byte2 = int(g[1])

	length = size - byte1
	if byte2 is not None:
		length = byte2 - byte1

	def generate():
		f = open(path, 'rb')
		f.seek(byte1)
		while True:
			data = f.read(65536)
			if not data:
				break
			yield data
		f.close()

	rv = Response(generate(), 206, mimetype=mimetype, direct_passthrough=True)
	rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
	return rv

@app.route("/config")
def config():
	return jsonify({"version" : 9,
					"serverName" : "Tsuki",
					"serverUuid" : str(uuid.uuid3(uuid.NAMESPACE_URL, request.host)),
					"address" : "http://" + request.host,
					"listEndpoint" : "http://" + request.host + "/list"
					})

@app.route("/list", methods=["GET", "POST"])
def listing():
	jlist = list()
	for filename in file_list.keys():
		jlist.append({"name" : filename,
					  "parentPath" : "/s/C::VR/",
					  "filePath" : "http://" + request.host + "/s/C::VR/" + filename,
					  "duration" : file_list[filename]["duration"],
					  "fileSize" : file_list[filename]["fileSize"],
					  "thumbnailPath" : "http://" + request.host + "/thumbnail/s/C::VR/" + filename + ".jpg",
					  "subtitles" : [],
					  })
	return jsonify({"code" : 1, "message" : "Success", "result": jlist})

@app.route("/thumbnail/s/C::VR/<filename>.jpg")
def thumbnail(filename):
	if os.path.isfile(file_list[filename]["localPath"] + ".jpg"):
		return send_file(file_list[filename]["localPath"] + ".jpg", mimetype='image/jpeg')
	else:
		abort(404)

@app.route("/s/C::VR/<filename>")
def video(filename):
	return send_file_partial(file_list[filename]["localPath"], file_list[filename]["mimeType"])

@app.after_request
def after_request(response):
	response.headers.add('Accept-Ranges', 'bytes')
	return response

if __name__ == "__main__":
	import sys
	import socket

	if len(sys.argv) > 1:
		directory = sys.argv[1]
	else:
		directory = "."

	generate_file_list(directory)
	if len(file_list) == 0:
		print "No files found, try specifying a directory with the first argument."
		sys.exit(1)

	lan_ip = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
	app.run(host=lan_ip, port=20066, threaded=True)

