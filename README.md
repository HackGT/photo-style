# HackGStyle

Style transfer models and photobooth infrastructure.

The style transfer model is modified from [PyTorch/examples](https://github.com/pytorch/examples)
 and is located under the `fast_neural_style` directory along with the original
 license and readme.

For 'quick out of the box' localhost setup:
# BACKEND:
	- Use paperspace! (DL box is has versions that are too new)
	- ./setup.sh
	- Load appropriate env vars:
		- SENDGRID_API_KEY
		- FROM_EMAIL
		- CLOUD_BUCKET (new one should be made per event)
		- Export service key json filename:
			- export GOOGLE_APPLICATION_CREDENTIALS=<key.json>
			- https://cloud.google.com/storage/docs/reference/libraries#client-libraries-install-cpp (export/load into a file)
	- open port, include port in address (test server up using simple get)
		- sudo ufw status verbose
		- sudo ufw allow <port>/tcp
	- python server.py
	- Startup the backend server, link the proper address in frontend

# FRONTEND:
	- Clone this repo and nfc-badge-server on serving laptop 
	- Use nvm to get node, npm i, npm run build
	- Start nfc-badge-server and follow appropriate instructions
		- if registered, starting the server will output nfc id
	- Load env vars:
		- REGISTRATION_API_KEY (find in admin panel)
		- REGISTRATION_URL (graphql for registration, make sure it's non-redirect)
		- CHECKIN_API_KEY [?]
		- CHECKIN_URL (non redirect)
	- Use python3/pip3 to install everything
	- python3 app.py
		- access via localhost to avoid insecure origins on chrome
	- Ready camera should log 'ready to capture...'