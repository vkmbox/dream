import logging

from df_engine.core import Context, Actor
import common.dff.integration.response as int_rsp
import common.dff.integration.context as int_ctx

TOPIC_DIALOGS_PATH = os.getenv("TOPIC_DIALOGS_PATH")
NP_DIALOGS_PATH = os.getenv("NP_DIALOGS_PATH")
TOPIC_DIALOGS = json.load(open(TOPIC_DIALOGS_PATH))
NP_DIALOGS = json.load(open(NP_DIALOGS_PATH))

logger = logging.getLogger(__name__)
# ....


def batch_processing_response(ctx: Context, actor: Actor, *args, **kwargs) -> str: 

    st_time = time.time()
    #dialogs_batch = request.json["dialogs"]

    final_confidences = []
    final_responses = []
    final_attributes = []

#    for dialog in dialogs_batch:
    dialog = int_ctx.get_dialog(ctx, actor)

    bot_response = "I really do not know what to answer."
    confidence = 0.0
    dialog_position, dialog_id, dialog_type = -1, "", ""
    attr = {}

    if len(dialog["bot_utterances"]) > 0:
        last_active_skill = dialog["bot_utterances"][-1]["active_skill"]
    else:
        last_active_skill = ""

    if last_active_skill in ["dummy_skill", "dummy_skill_dialog"]:

        if last_active_skill == "dummy_skill":
            text = dialog["bot_utterances"][-1]["text"]
            for key, value in TOPIC_DIALOGS.items():
                if text == value[0]:
                    dialog_id = key
                    dialog_type = "topic"
                    break
            for key, value in NP_DIALOGS.items():
                if text == value[0]:
                    dialog_id = key
                    dialog_type = "noun_phrase"
                    break
            dialog_position = 1
        else:
            for hypothesis in dialog["human_utterances"][-2]["hypotheses"]:
                if hypothesis["skill_name"] == "dummy_skill_dialog":
                    dialog_position = hypothesis["dialog_position"]
                    dialog_id = hypothesis["dialog_id"]
                    dialog_type = hypothesis["dialog_type"]

        if dialog_type in ["topic", "noun_phrase"]:

            if dialog_type == "topic":
                anticipated_dialog = TOPIC_DIALOGS[dialog_id]
            else:
                anticipated_dialog = NP_DIALOGS[dialog_id]

            human_response = dialog["human_utterances"][-1]["text"]
            anticipated_response = anticipated_dialog[dialog_position]
            human_response_encoded = normalize(encode([human_response]))[0]
            anticipated_response_encoded = normalize(encode([anticipated_response]))[0]

            score = human_response_encoded.dot(anticipated_response_encoded.T)

            if score > 0.5 and len(anticipated_dialog) - 2 > dialog_position:
                bot_response = anticipated_dialog[dialog_position + 1]
                confidence = float(score)
                dialog_position += 2

        attr = {"dialog_position": dialog_position, "dialog_id": dialog_id, "dialog_type": dialog_type}

    final_responses.append(bot_response)
    final_confidences.append(confidence)
    final_attributes.append(attr)

    total_time = time.time() - st_time
    logger.warning(f"dummy_skill_dialog exec time: {total_time:.3f}s")
#    return jsonify(list(zip(final_responses, final_confidences, final_attributes)))
    return int_rsp.multi_response(
        replies=final_responses,
        confidences=final_confidences,
#        human_attr=curr_human_attrs,
#        bot_attr=curr_bot_attrs,
        hype_attr=final_attributes,
    )(ctx, actor, *args, **kwargs)

#def batch_processing_confidence(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
#    _, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))
#    int_ctx.set_confidence(ctx, actor, confidence)
#    return ctx