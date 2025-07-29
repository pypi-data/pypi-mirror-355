from aiogram import Bot, Dispatcher, types, Router
from .tg_environment.t_user import TUser
from .taalc_bot import TaalcBot
from re import Match
import traceback
from aiogram.types import ChatMemberUpdated
from aiogram.types import Message, Update
from .teest.testing_message import TestingMessage

async def handle_with_tests(handler, message, match=None):
    try:
        user = TUser.user_by_tg_user(message.from_user)
        test_reply = message.reply_to_message
        if TaalcBot.testers:
            if message.reply_to_message:
                reply = message.reply_to_message
                test_reply = TestingMessage(
                    text = reply.text,
                    message_id = reply.message_id,
                    date = reply.date,
                    chat = reply.chat,
                    message_thread_id = reply.message_thread_id,
                    from_user = reply.from_user,
                    via_bot = reply.via_bot,
                    reply_to_message=reply.reply_to_message
                ).as_(reply.bot)
            message = TestingMessage(
                text = message.text,
                message_id = message.message_id,
                date = message.date,
                chat = message.chat,
                message_thread_id = message.message_thread_id,
                from_user = message.from_user,
                via_bot = message.via_bot,
                reply_to_message=test_reply
            ).as_(message.bot)
        
        if match:
            result =  await handler(message, user, match)
        else:
            result =  await handler(message, user)

        if TaalcBot.testers and not result:
            print(f"{handler.__name__} doesn't return any result")

        return result
    
    except Exception as ex:
        tb = traceback.format_tb(ex.__traceback__)
        tb = "\n".join(tb)
        err_msg = f'{ex}\n {tb}'
        if TaalcBot.error_prefix:
            err_msg = f'{TaalcBot.error_prefix}: {err_msg}'
        await message.reply(err_msg)                    
        raise ex


def msg_handler(*args):
    def handler_wrapper(handler):

        async def wrapper(message: types.Message, match: Match):
            # if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            result = await handle_with_tests(handler, message, match)
            return result
        
        for route in args:
            TaalcBot.msg_handlers[route] = wrapper
        return wrapper
    return handler_wrapper


def cmd_handler(*args):
    def handler_wrapper(handler):

        async def wrapper(message: types.Message):
            
            result = await handle_with_tests(handler, message)
            return result
        
        for route in args:
            TaalcBot.cmd_handlers[route] = wrapper
        return wrapper
    return handler_wrapper

async def _on_member_updated(event: ChatMemberUpdated, handler):
    try:
        user = TUser.user_by_tg_user(event.new_chat_member.user)                
        result =  await handler(event, user)
        
        return result
    except Exception as ex:
        tb = traceback.format_tb(ex.__traceback__)
        tb = "\n".join(tb)
        err_msg = f'{ex}\n {tb}'
        if TaalcBot.error_prefix:
            err_msg = f'{TaalcBot.error_prefix}: {err_msg}'
        await event.answer(err_msg)                    
        raise ex
    

def join_handler(handler):
    async def wrapper(event: ChatMemberUpdated):
        return await _on_member_updated(event, handler)
    TaalcBot.join_handlers.append(wrapper)
        
    return wrapper


def leave_handler(handler):
    async def wrapper(event: ChatMemberUpdated):
        return await _on_member_updated(event, handler)
    TaalcBot.leave_handlers.append(wrapper)
        
    return wrapper


def promoted_handler(handler):
    async def wrapper(event: ChatMemberUpdated):
        return await _on_member_updated(event, handler)
    TaalcBot.promoted_handlers.append(wrapper)
        
    return wrapper

def reaction_handler(handler):
    async def wrapper(reaction: types.MessageReactionUpdated):
        try:
            user = TUser.user_by_tg_user(reaction.user)
            result =  await handler(reaction, user)
            
            return result
        except Exception as ex:
            tb = traceback.format_tb(ex.__traceback__)
            tb = "\n".join(tb)
            err_msg = f'{ex}\n {tb}'
            if TaalcBot.error_prefix:
                err_msg = f'{TaalcBot.error_prefix}: {err_msg}'
             
            await reaction.bot.send_message(reaction.chat.id, err_msg)                    
            raise ex
    TaalcBot.reaction_handlers.append(wrapper)
        
    return wrapper