# Tsuki (&#26376;)

Tsuki is a simple streaming video server meant to be used with the Moon VR Player smartphone app.
It has been tested on Linux, but probably works on other platforms as well.

### Prerequisites

* Python 2.7 (https://www.python.org/)
* Flask (http://flask.pocoo.org/)
* ffprobe (from the FFmpeg suite, https://ffmpeg.org/)

### Usage

Simply run the tsuki.py Python script.

By default it looks for video files in the current directory. The first argument can be used to specify another directory.
It attempts to figure out the IP address of the LAN Ethernet interface automatically.

### License

Released into the public domain.
