#!/usr/bin/env python

import logging
import time
import re

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []

    for dialog in dialogs_batch:
        response, confidence, human_attr, bot_attr = process_info(
            dialog, which_info="name")

        if confidence == 0.0:
            response, confidence, human_attr, bot_attr = process_info(
                dialog, which_info="homeland")

        if confidence == 0.0:
            response, confidence, human_attr, bot_attr = process_info(
                dialog, which_info="location")

        if confidence == 0.0:
            response, confidence = tell_my_info(dialog, which_info="name")

        if confidence == 0.0:
            response, confidence = tell_my_info(dialog, which_info="location")

        if confidence == 0.0:
            response, confidence = tell_my_info(dialog, which_info="homeland")

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)

    total_time = time.time() - st_time
    logger.info(f'personal_info_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes)))


def process_info(dialog, which_info="name"):
    human_attr = {}
    bot_attr = {}
    response = ""
    confidence = 0.0

    curr_user_uttr = dialog["utterances"][-1]["text"].lower()
    curr_user_annot = dialog["utterances"][-1]["annotations"]
    try:
        prev_bot_uttr = dialog["utterances"][-2]["text"].lower()
    except IndexError:
        prev_bot_uttr = ""

    is_about_templates = {
        "name": (re.search(r"(what is|what's|whats|tell me) your? name",
                           prev_bot_uttr) or re.search(r"(my (name is|name's)|call me)",
                                                       curr_user_uttr)),
        "homeland": re.search(r"(where are you from|where you (were|was) born|"
                              r"(what is|what's|whats|tell me) your "
                              r"(home\s?land|mother\s?land|native\s?land|birth\s?place))",
                              prev_bot_uttr) or re.search(
            r"(my ((home\s?land|mother\s?land|native\s?land|birth\s?place) "
            r"is|(home\s?land|mother\s?land|native\s?land|birth\s?place)'s)|"
            r"(i was|i were) born in|i am from)",
            curr_user_uttr),
        "location": re.search(
            r"((what is|what's|whats|tell me) your? location|"
            r"where do you live|where are you now|"
            r"is that were you live now)",
            prev_bot_uttr) or re.search(
            r"(my (location is|location's)|(i am|i'm|i)( live| living)? in([a-zA-z ]+)?now)",
            curr_user_uttr)
    }
    repeat_info_phrases = {"name": "I didn't get your name. Could you, please, repeat it.",
                           "location": "I didn't get your location. Could you, please, repeat it.",
                           "homeland": "I didn't get your homeland. Could you, please, repeat it."}

    response_phrases = {"name": f"Nice to meet you. I will remember your name, ",
                        "location": f"Cool! I will remember your location is ",
                        "homeland": f"Cool! Is that were you live now?"}

    got_info = False
    # if user doesn't want to share his info
    if (is_about_templates[which_info] or prev_bot_uttr == repeat_info_phrases[which_info]) and curr_user_annot.get(
            "intent_catcher", {}).get("no", {}).get("detected", 0) == 1:
        response = "As you wish."
        confidence = 1.0
        return response, confidence, human_attr, bot_attr

    if re.search(r"is that were you live now",
                 prev_bot_uttr) and curr_user_annot.get("intent_catcher",
                                                        {}).get("yes", {}).get("detected", 0) == 1:
        logger.info(f"Found location=homeland")
        human_attr["location"] = dialog["human"]["profile"]["location"]
        response = f"Cool! I will remember your location is {human_attr['location']}."
        confidence = 10.0
        got_info = True
    elif re.search(r"is that were you live now",
                   prev_bot_uttr) and curr_user_annot.get("intent_catcher",
                                                          {}).get("no", {}).get("detected", 0) == 1:
        logger.info(f"Found location is not homeland")
        response = f"So, where do you live now?"
        confidence = 10.0
        got_info = False

    if is_about_templates[which_info] or prev_bot_uttr == repeat_info_phrases[which_info] and not got_info:
        logger.info(f"Asked for {which_info} in {prev_bot_uttr}")
        for ent in curr_user_annot.get("ner", []):
            if not ent:
                continue
            ent = ent[0]
            logger.info(f"Found {which_info} `{ent['text']}`")
            human_attr[which_info] = " ".join([n.capitalize() for n in ent["text"].split()])
            if which_info in ["name", "location"]:
                response = response_phrases[which_info] + human_attr[which_info] + "."
            elif which_info in ["homeland"]:
                if dialog["human"]["profile"].get("location", None) is None:
                    response = response_phrases[which_info]
                else:
                    response = f"Cool! I will remember your homeland is {human_attr[which_info]}."
            else:
                pass

            confidence = 10.0
            got_info = True
        if not got_info:
            if prev_bot_uttr == repeat_info_phrases[
                which_info] and curr_user_annot.get("intent_catcher",
                                                    {}).get("no", {}).get("detected", 0) == 1:
                response = ""
                confidence = 0.0
            else:
                response = repeat_info_phrases[which_info]
                confidence = 10.0
    return response, confidence, human_attr, bot_attr


def tell_my_info(dialog, which_info="name"):
    response = ""
    confidence = 0.0

    curr_user_uttr = dialog["utterances"][-1]["text"].lower()

    tell_my_templates = {"name": re.search(r"((what is|what's|whats|tell me|you know|you remember|memorize|say) "
                                           r"my name|"
                                           r"how( [a-zA-z ]+)?call me)",
                                           curr_user_uttr),
                         "location": re.search(r"((what is|what's|whats|tell me|you know|you remember|memorize|say) "
                                               r"my location|"
                                               r"where (am i|i am)(\snow)?)",
                                               curr_user_uttr),
                         "homeland": re.search(r"((what is|what's|whats|tell me|you know|you remember|memorize|say) "
                                               r"my (home\s?land|mother\s?land|native\s?land|birth\s?place)|"
                                               r"where (am i|i am) from)",
                                               curr_user_uttr)}

    responses = {"name": f"Sorry, we are still not familiar. What is your name?",
                 "location": f"Sorry, I don't have this information. But you can tell me. What is your location?",
                 "homeland": f"Sorry, I don't have this information. But you can tell me. Where are you from?"}
    if tell_my_templates[which_info]:
        logger.info(f"Asked to memorize user's {which_info} in {curr_user_uttr}")
        if dialog["human"]["profile"].get(which_info, None) is None:
            response = responses[which_info]
            confidence = 10.0
        else:
            name = dialog["human"]["profile"][which_info]
            response = f"Your {which_info} is {name}."
            confidence = 10.
    return response, confidence


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)