from aiogram.types import Message, Update
from ..taalc_bot import TaalcBot


    
class TestingMessage(Message):
    # _testing_msg: Message

    async def _notify(self, message):
        if TaalcBot.testers:
            upd = Update(update_id=1, message=message)
            for tester in TaalcBot.testers:
                await tester.dsp.feed_update(tester.bot, upd)

    async def reply(self, text, *args, parse_mode=None, **kwargs):
        res = None
        try:
            res = await super().reply(*args, text, **kwargs, parse_mode=parse_mode)            
        except Exception as ex:
            text = f'<blockquote>replied from {self.from_user.full_name}:\n{self.text}</blockquote>\n{text}'
            res = await super().answer(*args, text, **kwargs, parse_mode='html')            
        finally:
            await self._notify(res)
            return res


    async def answer(self, text, *args, parse_mode=None, **kwargs):
        res = await super().answer(*args, text, **kwargs, parse_mode=parse_mode)
        await self._notify(res)
        return res