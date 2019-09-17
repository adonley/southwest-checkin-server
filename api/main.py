from flask import Flask, request, jsonify
import redis
import os
import json
import logging


r = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'), port=6379)
app = Flask(__name__)


@app.route('/confirmation', methods=['POST'])
def submit_confirmation():
    data = json.loads(request.data)

    # Validate
    errors = []
    if not data.get('firstName'):
        errors.append('provide a first name')
    if not data.get('lastName'):
        errors.append('provide a last name')
    if not data.get('confirmation'):
        # TODO: check size
        errors.append('provide a confirmation')
    # TODO: Validate futher?
    # TODO: validate against API?
    # Bail if we have errors
    if len(errors) > 0:
        return jsonify({"errors": errors}), 400

    # r.sadd()
    # TODO: put in key for date UTC?
    # TODO: put in for confirmation
    # TODO: key expiration?
    r.set(data.get('confirmation', json.dumps(data)))
    return "", 201


@app.route('/confirmation/<code>', methods=['GET'])
def get_confirmation(code: str):
    app.logger.info("Get request through docker")
    confirmation = r.get(code)
    # validate existence
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    return jsonify(confirmation), 200


@app.route('/confirmation/<code>', methods=['DELETE'])
def delete_confirmation(code: str):
    # validate existence
    confirmation = r.get(code)
    if not confirmation:
        return jsonify({"errors": ["confirmation not found"]}), 400
    resp = r.delete(code)
    # TODO: delete from day key set.
    # No keys affected
    if int(resp) == 0:
        return jsonify({"errors": ["could not delete confirmation"]}), 500
    return jsonify(confirmation), 200


@app.route('/health', methods=['GET'])
def health():
    test_string = "I'm a goose"
    resp = r.echo(test_string)
    app.logger.info(resp)
    if resp != test_string:
        return jsonify({"status": "down"}), 500
    return jsonify({"status": "ok"}), 200


if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run()
