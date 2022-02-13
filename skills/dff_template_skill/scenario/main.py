import logging
import re

from df_engine.core.keywords import LOCAL, PROCESSING, TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl

import common.dff.integration.processing as int_prs
#import common.dff.integration.response as int_rsp


import common.constants as common_constants

from . import response as loc_rsp

logger = logging.getLogger(__name__)

flows = {
    "service": {
        "start": {RESPONSE: ""},
        "fallback": {RESPONSE: "", PROCESSING: {"set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE)}},
    },
    GLOBAL: {
        TRANSITIONS: {
            ("active_skill_driven_response", "dialogs_batch_processing"): cnd.true(),
        }
    },
    "active_skill_driven_response": {
        "dialogs_batch_processing": {
            RESPONSE: loc_rsp.batch_processing_response,
            TRANSITIONS: {lbl.repeat(): cnd.true()},
        },
    }
}

actor = Actor(flows, start_label=("service", "start"), fallback_label=("service", "fallback"))
