from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = os.environ.get('HOSTNAME', 'unknown')
    return f'''
    <h1>Hello World!</h1>
    <p>Running on Kubernetes v2</p>
    <p>Pod: {hostname}</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
