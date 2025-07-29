from epure import epure
from .t_offer import TOffer
from ..tg_environment.t_message import TMessage

@epure()
class MessageOffer(TOffer):
    subject: TMessage