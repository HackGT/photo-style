from flask import Flask, render_template
import os

app = Flask(__name__, static_url_path='/')

@app.route('/')
def root():
    return render_template( "index.html")

if __name__ == "__main__":
    app.debug = True
    # app.run()
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
