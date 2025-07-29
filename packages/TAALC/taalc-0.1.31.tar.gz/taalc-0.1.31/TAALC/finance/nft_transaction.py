from epure import epure
from .taalc_transaction import TaalcTransaction
from .taalc_nft import TaalcNft
from .taalc_nft_token import TaalcNftToken
# from .currency_transaction import CurrencyTransaction
# from epure import Elist


class NftTransaction(TaalcTransaction):    
    taalc_nft_token: TaalcNftToken
    amount: int    

    def __init__(self, sent_from, sent_to, taalc_nft_token, transaction_batch=None, amount=1):
        super().__init__()

        self.sent_from = sent_from
        self.sent_to = sent_to
        self.taalc_nft_token = taalc_nft_token
        self.transaction_batch = transaction_batch
        self.amount = amount