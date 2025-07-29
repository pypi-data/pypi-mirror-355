from .taalc_nft_token import TaalcNftToken
from epure import epure
from ..tg_environment.t_message import TMessage

@epure()
class MessageNftToken(TaalcNftToken):
    subject: TMessage