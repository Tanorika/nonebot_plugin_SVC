from nonebot.rule import to_me
from nonebot import on_command
from pathlib import Path
import langid
import asyncio
import datetime
import shutil
import winreg
import json
import sys
sys.path.append('nonebot_plugin_SVC')
from .bot import texttosound
import os,re
from nonebot.adapters.cqhttp import MessageSegment
current_path = os.path.dirname(__file__)
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    MessageSegment,
)
#加载模型配置
with open(current_path+'\\models.json',encoding='utf-8') as f:
    config=json.load(f)
characterlist=[]
for name in config.keys():
        characterlist.append(name)
#默认使用的模型
defalt='defaltmodel'
time=datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
desktoppath = winreg.QueryValueEx(key, "Desktop")[0]

async def send_to_tts(msg,character):
    if character in config:
        spk_list=[0]
        model_path = config[character]['model_path']
        config_path = config[character]['config_path']
        if 'cluster_model_path' in config[character]:
            cluster_model_path = config[character]['cluster_model_path']
        else:
            cluster_model_path = ""
        #检测语言
        language=langid.classify(msg)
        langcode=language[0]
        if(langcode=="zh"):
            voice =config[character]['voice_zh']
        elif(langcode=="en"):
            voice = config[character]['voice_en']
        elif(langcode=="ja"):
            voice = config[character]['voice_ja']
        else:
            voice = config[character]['voice']
        await texttosound(spk_list,model_path,config_path,cluster_model_path,voice,msg)
    else:
        return 'NotFound'
    

reply = on_command("/说",rule = to_me(), priority=99, block=False)
@reply.handle()
async def _(event: MessageEvent):
    # 获取消息文本
    msg = str(event.get_message())
    # 去掉带中括号的内容(去除cq码)
    msg = re.sub(r"\[.*?\]|\s*", "", msg)
    msg=msg.replace("/说","", 1)
    if(await send_to_tts(msg,defalt)!='NotFound'):
        await reply.finish(MessageSegment.record(Path(current_path+"\\results\\qqbot.wav")))
    else:
        await reply.finish(MessageSegment.text('唔……说不出，检查一下是不是默认模型设置出错了'))


change = on_command("/让",rule = to_me(), priority=99, block=False)
@change.handle()
async def _(event: MessageEvent):
    # 获取消息文本
    msg = str(event.get_message())
    # 去掉带中括号的内容(去除cq码)
    msg = re.sub(r"\[.*?\]|\s*", "", msg)
    parts=msg.split("说")
    character= parts[0][2:]
    if character.isdigit()==True :
        character = characterlist[int(character)-1]
    msg= parts[1]
    preview=msg[:10]
    if(await send_to_tts(msg,character)!='NotFound'):
        await change.finish(MessageSegment.record(Path(current_path+"\\results\\qqbot.wav")))
    else:
        await change.finish(MessageSegment.text('唔……是不是打错名称了？'))


save = on_command("/存",rule = to_me(), priority=99, block=False)
@save.handle()
async def _(event: MessageEvent):
    # 获取消息文本
    msg = str(event.get_message())
    # 去掉带中括号的内容(去除cq码)
    msg = re.sub(r"\[.*?\]|\s*", "", msg)
    parts=msg.split("说")
    character= parts[0][2:]
    if character.isdigit()==True :
        character = characterlist[int(character)-1]
    msg= parts[1]
    preview=msg[:10]
    if(await send_to_tts(msg,character)!='NotFound'):
        if not os.path.exists(desktoppath+"\\QQBotSave\\"):
            os.mkdir(desktoppath+"\\QQBotSave\\")
        shutil.copy(current_path+"\\results\\qqbot.wav",desktoppath+"\\QQBotSave\\")
        os.rename(desktoppath+"\\QQBotSave\\"+"qqbot.wav",desktoppath+"\\QQBotSave\\"+character+"-"+preview+"-"+time+".wav")
        await save.finish(MessageSegment.record(Path(current_path+"\\results\\qqbot.wav")))
    else:
        await save.finish(MessageSegment.text('唔……是不是打错名称了？'))


Listname = on_command("/列表",aliases={"/声音列表"},rule = to_me(), priority=99, block=False)
@Listname.handle()
async def _():
    number=0
    msg=""
    for name in config.keys():
        number=number+1
        msg+=str(number)+"."+name+"\n"
    await Listname.finish(MessageSegment.text("以下是支持的声音列表:\n"+msg+"\n使用指令“/让……说 内容”可以用不同声音输出，用序号表示也可以\n例：让1说 你好\n直接/说 内容 默认使用瑶瑶\n使用“/存……说 可将录音保存至服务器桌面并发送录音”"))