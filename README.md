# HackGStyle

Style transfer models and photobooth infrastructure.

The style transfer model is modified from [PyTorch/examples](https://github.com/pytorch/examples)
 and is located under the `fast_neural_style` directory along with the original
 license and readme.

For quick out of the box localhost setup:
	- clone this repo and badge repo on client, this repo on server
	- backend server needs to run w/ gpu
		- update ssh to https clone if necessary, submodule sync,
			- git submodule update --init --recursive
		- do setup necessary for detectron
	- Startup the backend server, link the proper address in frontend
	- Start frontend flask server, access via localhost to avoid insecure origins on chrome
	- Start nfc-badge-server and follow appropriate instructions

- TODO: write some setup scripts
	- backend:
		- conda env
		- pytorch .4
		- cuda 9.0
		- . make.sh
		- pip install
			- flask
			- flask_cors
			- sendgrid
			- google-cloud-storage
			- python-dotenv
			- pillow
			- scikit-image
			- opencv-python
			- packaging
			- yaml
			- pycocotools
	  