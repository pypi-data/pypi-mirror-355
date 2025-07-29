from .nft_transaction import NftTransaction
from epure import epure
from .message_nft_token import MessageNftToken

@epure()
class MessageTransaction(NftTransaction):
    taalc_nft_token: MessageNftToken 