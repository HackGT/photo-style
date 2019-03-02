# HackGStyle

Style transfer models and photobooth infrastructure.

The style transfer model is modified from [PyTorch/examples](https://github.com/pytorch/examples)
 and is located under the `fast_neural_style` directory along with the original
 license and readme.

For quick out of the box localhost setup:
		- Startup the backend server, link the proper address in frontend
		- Start frontend flask server, access via localhost to avoid insecure origins on chrome
		- Start nfc-badge-server and follow appropriate instructions