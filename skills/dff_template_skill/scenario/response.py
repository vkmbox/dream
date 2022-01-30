import logging

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)
# ....


def batch_processing_response(ctx: Context, actor: Actor, *args, **kwargs) -> str: 

    response = ""
    return response

def batch_processing_confidence(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
    _, confidence = get_detected_intents(int_ctx.get_last_human_utterance(ctx, actor))
    int_ctx.set_confidence(ctx, actor, confidence)
    return ctx