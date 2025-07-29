from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from ..taalc_bot import TaalcBot
import asyncio
from .bot_response import BotResponse
from .testing_message import TestingMessage
from ..tg_environment.t_user import TUser

class Tester:
    bot: Bot
    test_chat_id: int
    dsp: Dispatcher
    tested_bot: TaalcBot
    response: BotResponse
    msg_event: asyncio.Event
    waiting_delay: int
    _t_user: TUser = None

    @property
    def t_user(self):
        if not self._t_user:
            self._t_user = TUser.user_by_tg_user(self.bot)
        return self._t_user
    
    async def handler(self, message: Message):
        msg_user = message.from_user
        if msg_user.is_bot and message.chat.id == self.test_chat_id and \
              msg_user.id == self.tested_bot.bot.id and not self.msg_event.is_set():
            
            message = TestingMessage(
                text = message.text,
                message_id = message.message_id,
                date = message.date,
                chat = message.chat,
                message_thread_id = message.message_thread_id,
                from_user = message.from_user,
                via_bot = message.via_bot,
                reply_to_message = message.reply_to_message
            )
            self.response.response = message
            self.response.is_responded = True
            self.msg_event.set()

    async def reply(self, replied_msg: Message, msg_text: str, parse_mode: str=None) -> BotResponse:
        # msg_text = f'<blockquote>replied from {replied_msg.from_user.full_name}:\n{replied_msg.text}</blockquote>\n{msg_text}'
        sent_msg = await self.bot.send_message(self.test_chat_id, msg_text, parse_mode=parse_mode)
        sent_msg = TestingMessage(
            text = sent_msg.text,
            message_id = sent_msg.message_id,
            date = sent_msg.date,
            chat = sent_msg.chat,
            message_thread_id = sent_msg.message_thread_id,
            from_user = sent_msg.from_user,
            via_bot = sent_msg.via_bot,
            reply_to_message = replied_msg
        )
        
        res = await self._msg(sent_msg, parse_mode)
        return res

    async def msg(self, msg_text: str, parse_mode: str=None) -> BotResponse:
        sent_msg = await self.bot.send_message(self.test_chat_id, msg_text, parse_mode=parse_mode)
        sent_msg = TestingMessage(
            text = sent_msg.text,
            message_id = sent_msg.message_id,
            date = sent_msg.date,
            chat = sent_msg.chat,
            message_thread_id = sent_msg.message_thread_id,
            from_user = sent_msg.from_user,
            via_bot = sent_msg.via_bot
        )
        
        return await self._msg(sent_msg, parse_mode)

    async def _msg(self, sent_msg: Message, parse_mode: str=None) -> BotResponse:
        

        self.response = BotResponse(sent_msg)
        self.msg_event = asyncio.Event()        
        
        async def waiter():
            await asyncio.sleep(self.waiting_delay)
            self.msg_event.set()

        wait_task = asyncio.create_task(waiter())
        self.dsp.message()(self.handler)        
        asyncio.create_task(self.dsp.start_polling(self.bot, skip_updates=True))
        
        upd = Update(update_id=1, message=sent_msg)
        await self.tested_bot.dsp.feed_update(self.tested_bot.bot, upd)
        # asyncio.gather(self.dsp.start_polling(self.bot, skip_updates=True), self.tested_bot._start())

        
        await self.msg_event.wait()
        wait_task.cancel()
        # await asyncio.sleep(3)
        await self.dsp.stop_polling()
        self.dsp.message.handlers.clear()

        return self.response
        

    def __init__(self, tester_bot_token: str, tested_bot: TaalcBot, test_chat_id: int,\
                 waiting_delay=10):
        
        self.bot = Bot(tester_bot_token)
        self.test_chat_id = test_chat_id
        self.dsp = Dispatcher()
        self.tested_bot = tested_bot
        self.waiting_delay = waiting_delay

        
        TaalcBot.testers.append(self)