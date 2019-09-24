#!/usr/bin/env python

import json
import logging
import os
import re
import numpy as np
import uuid

import requests
from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

COBOT_API_KEY = os.environ.get('COBOT_API_KEY')
COBOT_OFFENSIVE_SERVICE_URL = os.environ.get('COBOT_OFFENSIVE_SERVICE_URL')

if COBOT_API_KEY is None:
    raise RuntimeError('COBOT_API_KEY environment variable is not set')
if COBOT_OFFENSIVE_SERVICE_URL is None:
    raise RuntimeError('COBOT_OFFENSIVE_SERVICE_URL environment variable is not set')

headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': f'{COBOT_API_KEY}'}

toxicity_classes = {0: "non-toxic", 1: "toxic"}
blacklist_classes = {0: "not blacklist", 1: "blacklist"}


@app.route("/offensiveness", methods=['POST'])
def respond():
    user_states_batch = request.json['dialogs']
    user_list_sentences = [dialog["utterances"][-1]["annotations"]["sentseg"]["segments"]
                           for dialog in user_states_batch]

    user_sentences = []
    dialog_ids = []
    for i, sent_list in enumerate(user_list_sentences):
        for sent in sent_list:
            user_sentences.append(sent)
            dialog_ids += [i]
    session_id = uuid.uuid4().hex
    toxicities = []
    confidences = []
    blacklists = []

    result = requests.request(url=f'{COBOT_OFFENSIVE_SERVICE_URL}',
                              headers=headers,
                              data=json.dumps({'utterances': user_sentences}),
                              method='POST')
    if result.status_code != 200:
        msg = "result status code is not 200: {}. result text: {}; result status: {}".format(result, result.text,
                                                                                             result.status_code)
        sentry_sdk.capture_message(msg)
        logger.warning(msg)
        toxicities = [[]] * len(user_states_batch)
        confidences = [[]] * len(user_states_batch)
        blacklists = [[]] * len(user_states_batch)
    else:
        result = result.json()
        # result is an array where each element is a dict with scores
        result = np.array(result["offensivenessClasses"])
        dialog_ids = np.array(dialog_ids)

        for i, sent_list in enumerate(user_list_sentences):
            logger.info(f"user_sentence: {sent_list}, session_id: {session_id}")
            curr_toxicities = result[dialog_ids == i]

            curr_confidences = [float(t["values"][1]["confidence"]) for t in curr_toxicities]
            curr_blacklists = [blacklist_classes[t["values"][0]["offensivenessClass"]] for t in curr_toxicities]
            curr_toxicities = [toxicity_classes[t["values"][1]["offensivenessClass"]] for t in curr_toxicities]

            toxicities += [curr_toxicities]
            confidences += [curr_confidences]
            blacklists += [curr_blacklists]
            logger.info(f"sentiment: {curr_toxicities}")

    return jsonify(list(zip(toxicities, confidences, blacklists)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
