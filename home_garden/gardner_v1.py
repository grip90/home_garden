import sys
import time
import datetime
import telepot
import os
import RPi.GPIO as GPIO

water_pin = 4
options = """
help  - Displays this Message
photo - Click a pic
water - Water the plants now.
stop  - Stop watering today. It's raining (maybe)
start - restart watering \r\n"""

def fetch_cfg():
    hdl = open("/home/pi/home_garden/cfg.txt","r")
    data = hdl.readlines()
    hdl.close()
    t0 = data[0].split("#")[0].strip()
    t1 = data[1].split("#")[0].strip()
    t2 = data[2].split("#")[0].strip()
    dur = data[3].split("#")[0].strip()
    return t0,t1,t2,dur

def update_water_table(ret0,ret1,ret2):
    strval = str(ret0) + "\r\n" + str(ret1) + "\r\n" + str(ret2) + "\r\n"
    hdl = open("/home/pi/home_garden/watertable.txt","w")
    hdl.write(strval)
    hdl.close()
    
def fetch_watertable():
    hdl = open("/home/pi/home_garden/watertable.txt","r")
    data = hdl.readlines()
    hdl.close()
    w0 = int(data[0].strip())
    w1 = int(data[1].strip())
    w2 = int(data[2].strip())
    return w0,w1,w2
    
def check_timing(cfg_str,w):
    now_str = str(datetime.datetime.now()).split(' ')[1]
    now_hh_str  = now_str[0:2]
    now_mm_str  = now_str[3:5]
    cfg_hh_str  = cfg_str[0:2]
    cfg_mm_str  = cfg_str[2:4]
    retval = 0
    #print("Now:"+now_hh_str+now_mm_str+" Cfg:"+cfg_hh_str+cfg_mm_str)
    if (w == 0):
        if(int(now_hh_str) >= int(cfg_hh_str)):
            if(int(now_mm_str) >= int(cfg_mm_str)):
                retval = 1
                print("Match hh mm = ",now_hh_str,now_mm_str)
    if((now_hh_str == "00") and (now_mm_str == "00")):
       update_water_table(0,0,0)
    return retval;
    

def check_watering():
    t0,t1,t2,dur_str = fetch_cfg()
    w0,w1,w2 = fetch_watertable()
    dur = int(dur_str)
    ret0 = check_timing(t0,w0)
    ret1 = check_timing(t1,w1)
    ret2 = check_timing(t2,w2)
    #print("ret0: "+str(ret0) + "ret1: "+str(ret1) +"ret2: "+str(ret2))
    if(ret0 or ret1 or ret2):
        #Watering msg to client
        bot_send_msg_to_all("Water time on")
        print("water now quota")
        water_now(dur)
        #Send Photo
        bot_send_photo_to_all()
	ret0 = ret0 | w0
	ret1 = ret1 | w1
	ret2 = ret2 | w2
        update_water_table(ret0,ret1,ret2)
        bot_send_msg_to_all("Water time off")
    
def click_pic():
    try:
        os.system("fswebcam -D 2 -S 20 --set brightness=30% --set contrast 0% -r 640x480 /home/pi/home_garden/pic.jpg")
    except:
        pass
        
        
def gardner_init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(water_pin,GPIO.OUT)
    GPIO.setwarnings(False)

def water_now(dur):
    GPIO.output(water_pin,1)
    time.sleep(dur)
    GPIO.output(water_pin,0)

def bot_send_pic(chat_id):
    click_pic()
    bot.sendPhoto(chat_id,photo=open('/home/pi/home_garden/pic.jpg','rb'))
    
def bot_water_plants(chat_id):
    bot.sendMessage(chat_id,"bot_water_plants!")
    t0,t1,t2,dur_str = fetch_cfg()
    bot.sendMessage(chat_id,dur_str)
    dur = 30
    dur = int(dur_str)
    bot.sendMessage(chat_id,"watering !")
    water_now(dur)
    bot.sendMessage(chat_id,"watering done!")

def bot_show_options(chat_id):
    bot.sendMessage(chat_id,options)

def bot_send_photo_to_all():
    hdl = open("/home/pi/home_garden/register.txt","r")
    data = hdl.readlines()
    click_pic()    
    hdl.close()
    for chat_id in data:
        ide = int(chat_id)
        bot.sendPhoto(ide,photo=open('/home/pi/home_garden/pic.jpg','rb'))
        
def bot_send_msg_to_all(msg):
    hdl = open("/home/pi/home_garden/register.txt","r")
    data = hdl.readlines()
    hdl.close()
    for chat_id in data:
        ide = int(chat_id)
        bot.sendMessage(ide,msg)

def bot_register(ide):
    chat_id = str(ide)
    hdl = open("/home/pi/home_garden/register.txt","r")
    data = hdl.readlines()
    hdl.close()
    for line in data:
        if chat_id in line:
            return
    hdl = open("/home/pi/home_garden/register.txt","w")
    for line in data:
        hdl.write(line)
    hdl.write(chat_id)
    hdl.close()
    bot.sendMessage(chat_id,"Hello Registered!")
    print("Registered")
    

def handle(msg):
    #os.system("fswebcam img.jpg")
    chat_id = msg['chat']['id']
    command = msg['text']
    command = command.lower()
    print("Got a command")
    if command == "help":
        bot_show_options(chat_id)
    if command == 'hello':
        bot.sendMessage(chat_id,"Hello there!")
    if command == "photo":
        print("request pic")
        bot.sendMessage(chat_id,"Sending pic!")
        bot_send_pic(chat_id)        
        print("Send Success")
    if command == "water":
	bot.sendMessage(chat_id,"Watering request")
        bot_water_plants(chat_id)
    if command == "register":
        bot_register(chat_id)
    

gardner_init()
#Fill your secret Bot ID from Telegram BotFather here.
bot = telepot.Bot('##########')
bot.message_loop(handle)
print("Bot started")

while 1:
    time.sleep(10)
    try:
        check_watering()
    except:
        pass
    
