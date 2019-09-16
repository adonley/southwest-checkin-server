from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/confirmation', methods=['POST'])
def submit_confirmation():
    return


@app.route('/confirmation', methods=['GET'])
def get_confirmations():
    return


@app.route('/confirmation', methods=['DELETE'])
def delete_confirmation():
    return


if __name__ == '__main__':
    app.run()
