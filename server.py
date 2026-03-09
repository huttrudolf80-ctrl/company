from flask import Flask

app = Flask('')

@app.route('/')
def home():
  return "Bot active"

app.run(host="0.0.0.0", port=3000)
