#!/usr/bin/env python
import os
import re

import jwt
from flask import Flask, jsonify, render_template
from flask import current_app
from flask import request
from flask_rq import get_queue

app = Flask(__name__)


@app.route('/transaction', methods=['POST', 'GET'])
def create_transaction():

    if request.method == 'POST':

        token: str = request.form.get('token')
        amount: int = int(request.form.get('amount'))
        currency: str = request.form.get('currency')

        # if not token:
        #     return jsonify(error='Token is blank'), 422
        # if not amount:
        #     return jsonify(error='Amount is blank'), 422
        # if not currency:
        #     return jsonify(error='Currency is blank'), 422
        if not re.match(r'^[A-Z]{3}$', currency):
            #return jsonify(error='Invalid currency code'), 422
            return render_template('transaction.html', error='Invalid currency code')

        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=["HS256"])
        except jwt.InvalidTokenError as exc:
            return jsonify(error=str(exc)), 422
        else:
            if payload['can_transact']:
                get_queue().enqueue(
                    '__main__.record_transaction',
                    user_id=payload['user_id'],
                    amount=amount,
                    currency=currency,
                )
                return jsonify(
                    user_id=payload['user_id'],
                    amount=amount,
                    currency=currency,
                )
            else:
                #return jsonify(error='User cannot transact'), 403
                return render_template('transaction.html', error='User cannot transact')
    
    else:
        return render_template('transaction.html')

@app.route('/health')
def health():
    return jsonify(healthy=True)


if __name__ == '__main__':
    # Env
    redis_url: str = os.getenv('REDIS_URL', 'redis://169.10.0.10:6379/0')
    http_port: int = int(os.getenv('HTTP_PORT', 5000))
    jwt_secret: str = os.environ['JWT_SECRET']

    # Flask config
    app.config['RQ_DEFAULT_URL'] = redis_url
    app.config['JWT_SECRET'] = jwt_secret

    # Run app
    app.run(host='0.0.0.0', port=http_port, threaded=True)
