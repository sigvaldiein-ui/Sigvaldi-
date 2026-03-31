#!/usr/bin/env python3
import os,sys,threading,subprocess,time
from collections import defaultdict
from datetime import datetime
import telebot
from telebot import util
from dotenv import load_dotenv

BASE_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.append(BASE_DIR)
from core.agent_core_v4 import analyze_query,ask_llm
from skills.multimodal_reader import analyze_multimodal
from core.db_manager import (is_user_allowed,get_free_queries_left,nota_frja_prufu,
    skra_samtal,saekja_profile,uppfaera_profile,setja_upp_gagnagrunn)

load_dotenv(os.path.join(BASE_DIR,'config','.env'))
TELEGRAM_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
MASTER_ID=8547098998

bot=telebot.TeleBot(TELEGRAM_TOKEN,threaded=True,num_threads=5)
SANDBOX_DIR=os.path.join(BASE_DIR,"sandbox")
os.makedirs(SANDBOX_DIR,exist_ok=True)

MAX_MINNI=10
user_sessions=defaultdict(list)
memory_lock=threading.Lock()

SYSTEM_PROMPT="""Thu ert Mimir, rannsoknarforstjori Akademias - islenskur AI adstodarmadur.
REGLUR: Svaraou ALLTAF a islensku. Stutt og skyrt. Manst eftir samhengi. Aldrei bua til stadreyndir. Ef thu thekkir ekki nafn notandans, mattu spyrja kurteiislega um thad i edlilegu samhengi til ad gera spjallid personulegra."""

FLOKKUNAR_PROMPT="""Thu ert nakvamt flokkunarkerfi. Svaraou AETHEINS med einu ordi: SEARCH eda CHAT.
Daemi 1: "Saell Mimir, eg heiti Sigvaldi." -> CHAT
Daemi 2: "Hvad er nyjaста skjakortid fra NVIDIA?" -> SEARCH
Daemi 3: "Hver er stan a hlutabrefum Tesla i dag?" -> SEARCH
Daemi 4: "Geturdu dregid thessa ritgerd saman?" -> CHAT
Daemi 5: "Hvad sagdi eg ao eg heti adan?" -> CHAT
Daemi 6: "Finndu nyjastu frettir um gervigreind." -> SEARCH
Regla: Ef spurning krefst nyrra stadreynd: SEARCH. Jafnvel thott thu haldur ao thu vitir! Annars CHAT.
Beidni: {texti}
Svar (SEARCH eda CHAT):"""

def athuga_adgang(chat_id):
    if chat_id==MASTER_ID: return True,999
    try:
        if is_user_allowed(chat_id): return True,999
        frir=get_free_queries_left(chat_id)
        if frir>0:
            eftir=nota_frja_prufu(chat_id)
            return True,eftir
        return False,0
    except Exception: return True,5

def senda_greidslubod(chat_id):
    texti=("Thu hefur notad allar 5 friar prufur Mimis.\n\n"
        "Mimir er islenskt AI rannsoknarverkfaeri med:\n"
        "- Lokad herbergi - oll gogn eytt eftir hverja lotu\n"
        "- Ratsjartaekni - leitar a netid i rauntima\n"
        "- Fullkomid islensku\n\n"
        "Veldu pakka:\n"
        "Kynning: 990 kr/man\n"
        "Einstaklingsadgangur: 1.990 kr/man\n"
        "Midgildi: 4.990 kr/man\n"
        "Fyrirtaekjapakki: Serstatt\n\n"
        "Hafa samband: sigvaldi@fjarmalin.is")
    bot.send_message(chat_id,texti)

def senda_prufu_kynning(chat_id,frir):
    if frir==4: bot.send_message(chat_id,"Velkomin! 5 friar prufur. Mimir er lokad AI verkfaeri - oll gogn eytt eftir hverja lotu (Zero-Data).")
    elif frir==2: bot.send_message(chat_id,"2 friar prufur eftir. Til ad halda afram: sigvaldi@fjarmalin.is")
    elif frir==0: bot.send_message(chat_id,"Thetta var thinn sidasti frji svar. Til ad halda afram tharftu ad kaupa adgang.")

def smida_system_prompt(chat_id):
    try:
        profile=saekja_profile(chat_id)
        if not profile: return SYSTEM_PROMPT
        profile_texti=", ".join([f"{k}: {v}" for k,v in profile.items()])
        return f"{SYSTEM_PROMPT}\n\n[NOTANDI: {profile_texti}]"
    except Exception: return SYSTEM_PROMPT

def get_history(chat_id):
    with memory_lock: return list(user_sessions[chat_id])

def add_memory(chat_id,role,content):
    with memory_lock:
        user_sessions[chat_id].append({"role":role,"content":content})
        if len(user_sessions[chat_id])>MAX_MINNI: del user_sessions[chat_id][0]

def flokka_beidni(texti):
    try:
        res=ask_llm("Svaraou AETHEINS: SEARCH eda CHAT",FLOKKUNAR_PROMPT.format(texti=texti),temp=0.0)
        return "CHAT" if "CHAT" in res.upper() else "SEARCH"
    except: return "SEARCH"

def spjalla_med_minni(chat_id,texti):
    add_memory(chat_id,"user",texti)
    saga=get_history(chat_id)
    samtal="\n".join([f"{'Notandi' if s['role']=='user' else 'Mimir'}: {s['content']}" for s in saga])
    try:
        svar=ask_llm(smida_system_prompt(chat_id),samtal,temp=0.4)
        add_memory(chat_id,"assistant",svar)
        return svar
    except Exception as e: return f"Villa: {str(e)[:100]}"

def leita_og_muna(chat_id,texti):
    add_memory(chat_id,"user",f"[Leit]: {texti}")
    try:
        svar=analyze_query(texti)
        add_memory(chat_id,"assistant",f"[LEITARNIÐURSTAÐA]: {svar[:1500]}")
        return svar
    except Exception as e: return f"Villa i leit: {str(e)[:100]}"

def safe_reply(chat_id,msg_id,texti):
    if not texti: texti="Engin nidurstaeda."
    chunks=util.smart_split(texti,chars_per_string=3000)
    for i,chunk in enumerate(chunks):
        try:
            if i==0: bot.edit_message_text(chunk,chat_id=chat_id,message_id=msg_id,parse_mode="Markdown")
            else: bot.send_message(chat_id,chunk,parse_mode="Markdown")
        except:
            if i==0: bot.edit_message_text(chunk,chat_id=chat_id,message_id=msg_id)
            else: bot.send_message(chat_id,chunk)

@bot.message_handler(commands=['start','help'])
def welcome(m):
    bot.reply_to(m,"Mimir v8.0 Gatekeeper\n\nEg man eftir samtalinu og svarar a islensku.\nSendu texta, skjol, myndir, video eda raddskilabod.\n/gleymdu - hreinsa minni")

@bot.message_handler(commands=['gleymdu','reset'])
def gleymdu(m):
    with memory_lock: user_sessions[m.chat.id].clear()
    bot.reply_to(m,"Minni hreinsad!")

@bot.message_handler(content_types=['text'])
def handle_text(m):
    texti=m.text.strip()
    if texti.startswith('/'): return
    chat_id=m.chat.id
    leyfður,frir=athuga_adgang(chat_id)
    if not leyfður:
        senda_greidslubod(chat_id)
        return
    sm=bot.reply_to(m,"Mimir hugsar...")
    def run():
        try:
            flokkun=flokka_beidni(texti)
            if flokkun=="SEARCH":
                bot.edit_message_text("Kveiki a Ratsja...",chat_id=chat_id,message_id=sm.message_id)
                svar=leita_og_muna(chat_id,texti)
            else:
                svar=spjalla_med_minni(chat_id,texti)
            safe_reply(chat_id,sm.message_id,svar)
            if chat_id!=MASTER_ID: senda_prufu_kynning(chat_id,frir)
            try: skra_samtal(chat_id,flokkun)
            except: pass
        except Exception as e:
            try: bot.edit_message_text(f"Kerfisvilla: {str(e)[:200]}",chat_id=chat_id,message_id=sm.message_id)
            except: pass
    threading.Thread(target=run).start()

@bot.message_handler(content_types=['voice','audio','document','photo','video'])
def handle_files(m):
    chat_id=m.chat.id
    leyfður,frir=athuga_adgang(chat_id)
    if not leyfður:
        senda_greidslubod(chat_id)
        return
    sm=bot.reply_to(m,"Mottek skra...")
    def run():
        lp=""
        try:
            if m.content_type=='photo': fid=m.photo[-1].file_id
            elif m.content_type in ['audio','voice','document','video']: fid=getattr(m,m.content_type).file_id
            else: return
            fi=bot.get_file(fid)
            data=bot.download_file(fi.file_path)
            lp=os.path.join(SANDBOX_DIR,f"{m.content_type}_{m.message_id}.{fi.file_path.split('.')[-1]}")
            with open(lp,'wb') as f: f.write(data)
            bot.edit_message_text("Greini skra...",chat_id=chat_id,message_id=sm.message_id)
            svar=analyze_multimodal(lp,m.caption or "")
            add_memory(chat_id,"user",f"[Skra: {m.content_type}]")
            add_memory(chat_id,"assistant",f"[Greining]: {svar[:1500]}")
            if chat_id!=MASTER_ID: senda_prufu_kynning(chat_id,frir)
            try: skra_samtal(chat_id,"FILE")
            except: pass
            safe_reply(chat_id,sm.message_id,svar)
        except Exception as e:
            try: bot.edit_message_text(f"Villa: {str(e)[:200]}",chat_id=chat_id,message_id=sm.message_id)
            except: pass
        finally:
            if lp and os.path.exists(lp):
                try: subprocess.run(["shred","-u","-z",lp],check=True)
                except: os.remove(lp)
    threading.Thread(target=run).start()

if __name__=="__main__":
    setja_upp_gagnagrunn()
    print(f"Mimir v8.0 Gatekeeper raestur — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    # VORN GEGN 409 CONFLICT
    try:
        bot.remove_webhook()
        time.sleep(2)
        print("Webhook hreinsat - 409 vorn virk")
    except Exception as e:
        print(f"Webhook: {e}")
    bot.infinity_polling(skip_pending=True)
