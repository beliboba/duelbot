import random
import sqlalchemy
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle import Keyboard, BaseStateGroup, Text, KeyboardButtonColor, Callback, GroupEventType
from vkbottle.dispatch.rules.base import ReplyMessageRule


engine = sqlalchemy.create_engine("sqlite:///sqlite3.db")
engine.connect()
bot = Bot("vk1.a.XF_IQWGBvk2MpanQke1bnTx1dko0ko43QwI5Kk_gjsL_eczp6bnJnFYdeY81-Ja01eEKMqYX-wjNQu8SIto_rZAdOxd9UqKcKsD7QiyC9z7ug2fGKOOFFXqjzhE0Ali8iLbppmPIBs3d-m6l6n5xuauoEkQZ32QanG2x3-HpZjYHlCIl7bMO87Wrw9GSCSn5")
bot.labeler.vbml_ignore_case = True


duelkbd = (
	Keyboard(inline=True)
	.add(Callback("Согласиться", payload={"cmd": "accept"}), color=KeyboardButtonColor.POSITIVE)
	.add(Callback("Отказаться", payload={"cmd": "deny"}), color=KeyboardButtonColor.NEGATIVE)
	.get_json()
)


shootkbd = (
	Keyboard(inline=True)
	.add(Callback("Стрелять", payload={"cmd": "shoot"}), color=KeyboardButtonColor.PRIMARY)
	.add(Callback("Застрелиться", payload={"cmd": "suicide"}), color=KeyboardButtonColor.NEGATIVE)
)


class DuelStates(BaseStateGroup):
	pending = "pending"
	playing = "playing"
	turn = "turn"


@bot.on.message(ReplyMessageRule(), text="Дуэли <action>")
async def duel(msg: Message, action: str):
	user = await bot.api.users.get([msg.reply_message.from_id])
	if action.lower() == "заявка":
		if msg.reply_message.from_id != msg.from_id:
			if (await bot.state_dispenser.get(peer_id=msg.reply_message.from_id)) != "DuelStates:pending" and (await bot.state_dispenser.get(peer_id=msg.from_id)) != "DuelStates:playing":
				await bot.state_dispenser.set(peer_id=msg.reply_message.from_id, state=DuelStates.pending, enemy=msg.from_id)
				await bot.state_dispenser.set(peer_id=msg.from_id, state=DuelStates.playing, enemy=msg.reply_message.from_id)
				await msg.answer(f"[id{msg.reply_message.from_id}|{user[0].first_name}], тебя вызвали на дуэль!🔫", keyboard=duelkbd)
			else:
				await msg.answer()
		else:
			await msg.reply("Ты не можешь вызвать самого себя на дуэль👶")
	elif action.lower() == "профиль":
		await msg.reply("W.I.P.")
	else:
		await msg.reply("Тут все команды типа будут")


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def handler(event: MessageEvent):
	if event.payload == {"cmd": "accept"}:
		if (await bot.state_dispenser.get(peer_id=event.user_id)).state == "DuelStates:pending":
			await event.show_snackbar("Ты согласился!")
			user = await bot.api.users.get([event.user_id])
			await event.send_message(message=f"{user[0].first_name} согласился на дуэль!", keyboard=shootkbd)
			enemy = (await bot.state_dispenser.get(peer_id=event.user_id)).payload.get('enemy')
			await bot.state_dispenser.set(peer_id=event.user_id, state=DuelStates.turn, enemy=enemy)
		else:
			await event.show_snackbar("Ты не можешь сюда нажимать 😡")
	elif event.payload == {"cmd": "deny"}:
		if (await bot.state_dispenser.get(peer_id=event.user_id)).state == "DuelStates:pending":
			user = await bot.api.users.get([event.user_id])
			await event.send_message(message=f"{user[0].first_name} отказался от дуэли как лох последний!")
			await event.show_snackbar("Ты отказался")
			await bot.state_dispenser.delete(peer_id=event.user_id)
		else:
			await event.show_snackbar("Ты не можешь сюда нажимать 😡")

	elif event.payload == {"cmd": "shoot"}:
		if (await bot.state_dispenser.get(peer_id=event.user_id)).state == "DuelStates:turn":
			user = await bot.api.users.get([event.user_id])
			chance = bool(random.getrandbits(1))
			if chance:
				await event.send_message(
					f"[id{event.user_id}|{user[0].first_name}] стреляет и попадает!🔫 \nПобеда!")
				await bot.state_dispenser.delete(peer_id=event.user_id)
			else:
				enemy = (await bot.state_dispenser.get(peer_id=event.user_id)).payload.get('enemy')
				await bot.state_dispenser.set(peer_id=enemy, state=DuelStates.turn, enemy=event.user_id)
				await event.send_message(
					f"[id{event.user_id}|{user[0].first_name}] стреляет но не попадает!🔫 \nХод переходит к противнику!",
					keyboard=shootkbd)
		else:
			await event.show_snackbar("Чичас не твой ход!😡")
	else:
		await event.show_snackbar("Ты не можешь сюда нажимать 😡")


if __name__ == "__main__":
	bot.run_forever()
