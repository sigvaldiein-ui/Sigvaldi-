#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telegram_bot_v9_DEV.py
----------------------
Mímir DEV bot með Straumur paywall (Sprint 15.3).

BREYTINGAR (Sprint 15.3):
- Nýr import: payment_handler (Straumur Hosted Checkout)
- senda_greidslubod() → inline takkar með plan vali
- Nýr callback handler: plan val → Straumur checkout URL
- Ný skipun: /askrift — sýna verðskrá og velja plan
- Ný skipun: /stada — sýna notandastöðu (premium/fríar prufur)

BREYTINGAR (Sprint 15.4):
- agent_core_v4 skipt út fyrir agent_core_v5 (Supervisor/Router)
- Mímir getur nú leitað á netinu í raunstæðu með Deep Hunter
- Flokkun: SEARCH → Deep Hunter, CHAT → v4 kjarni

ATHUGASEMDIR:
- Þetta er DEV útgáfa — notar .env.dev
- Ósnertanlegar skrár: agent_core_v4.py, telegram_bot_v5.py, telegram_bot_v7_Omni.py
- Per vinnur ALLTAF í DEV, aldrei PROD
"""
import os,sys,threading,subprocess,time
from collections import defaultdict
from datetime import datetime
import telebot
from telebot import util
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

BASE_DIR=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.append(BASE_DIR)
# Sprint 15.4 — V5 Supervisor (importar v4 í gegnum v5)
try:
    from core.agent_core_v5 import MimirCoreV5
    MIMIR_V5 = MimirCoreV5()
    V5_VIRKUR = True
    print("✅ agent_core_v5 (Supervisor) hlaðinn")
except ImportError as e:
    V5_VIRKUR = False
    print(f"⚠️  agent_core_v5 vantar: {e} — nota v4 fallback")

# Fallback — alltaf hafa v4 til taðs
from core.agent_core_v4 import analyze_query,ask_llm
from skills.multimodal_reader import analyze_multimodal
from core.db_manager import (is_user_allowed,get_free_queries_left,nota_frja_prufu,
    skra_samtal,saekja_profile,uppfaera_profile,setja_upp_gagnagrunn,saekja_notanda)

# Sprint 15.3 — Straumur greiðslustjóri
try:
    from core.payment_handler import (bua_til_checkout, athuga_stodu,
        fa_verdskra_texta, fa_plan_upplysingar, VERDSKRA)
    STRAUMUR_VIRKUR = True
    print("✅ payment_handler hlaðinn")
except ImportError as e:
    STRAUMUR_VIRKUR = False
    print(f"⚠️  payment_handler vantar: {e} — paywall óvirkur")

load_dotenv(os.path.join(BASE_DIR,'config','.env.dev'))
TELEGRAM_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_TOKEN')
MASTER_ID=8547098998
import sys as _sys
_sys.path.append('/workspace/mimir_net/security')
_sys.path.append('/workspace/mimir_net/skills')

try:
    from input_sanitizer import is_safe_prompt, get_rejection_message
    SANITIZER_VIRKUR = True
except:
    SANITIZER_VIRKUR = False

try:
    from source_validator import score_sources, get_warning_text
    VALIDATOR_VIRKUR = True
except:
    VALIDATOR_VIRKUR = False


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


# =============================================================
# STRAUMUR PAYWALL — Sprint 15.3
# =============================================================

def senda_greidslubod(chat_id):
    """
    Sendir greiðslutilboð með inline takkum þegar fríar prufur klárast.
    Ef Straumur er ekki virkur → falla til baka í gamlan texta.
    """
    if not STRAUMUR_VIRKUR:
        # Fallback — gamli textinn ef payment_handler vantar
        texti=("Þú hefur notað allar 5 fríar prufur Mímis.\n\n"
            "Mímir er íslenskt AI rannsóknarverkfæri með:\n"
            "• Lokað herbergi — öll gögn eytt eftir hverja lotu\n"
            "• Ratsjártækni — leitar á netið í rauntíma\n"
            "• Fullkomið íslensku\n\n"
            "Hafa samband: sigvaldi@fjarmalin.is")
        bot.send_message(chat_id,texti)
        return

    # Straumur virkur — sýna verðskrá með inline takkum
    texti = ("🔒 Þú hefur notað allar 5 fríar prufur Mímis.\n\n"
             "Mímir er íslenskt AI rannsóknarverkfæri með:\n"
             "• Lokað herbergi — öll gögn eytt eftir hverja lotu\n"
             "• Ratsjártækni — leitar á netið í rauntíma\n"
             "• Fullkomið íslensku\n\n"
             "💰 *Veldu áskriftarpakka:*")

    # Búa til inline takka fyrir hvern pakka
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⭐ Kynning — 990 kr/mán", callback_data="plan_kynning"),
        InlineKeyboardButton("⭐ Einstaklingsaðgangur — 1.990 kr/mán", callback_data="plan_einstakling"),
        InlineKeyboardButton("💎 Miðgildi — 4.990 kr/mán", callback_data="plan_midgildi"),
    )

    try:
        bot.send_message(chat_id, texti, parse_mode="Markdown", reply_markup=markup)
    except:
        bot.send_message(chat_id, texti, reply_markup=markup)


def senda_prufu_kynning(chat_id,frir):
    if frir==4: bot.send_message(chat_id,"Velkomin! 5 fríar prufur. Mímir er lokað AI verkfæri — öll gögn eytt eftir hverja lotu (Zero-Data).")
    elif frir==2: bot.send_message(chat_id,"⏳ 2 fríar prufur eftir. Sláðu inn /askrift til að sjá áskriftarleiðir.")
    elif frir==0: bot.send_message(chat_id,"⏳ Þetta var þitt síðasta fría svar. Sláðu inn /askrift til að halda áfram.")


# =============================================================
# CALLBACK HANDLER — Straumur plan val
# =============================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def handle_plan_val(call):
    """Meðhöndlar þegar notandi smellir á áskriftartakka."""
    chat_id = call.message.chat.id
    plan = call.data.replace("plan_", "")

    if not STRAUMUR_VIRKUR:
        bot.answer_callback_query(call.id, "Greiðslukerfi óvirkt — hafa samband við sigvaldi@fjarmalin.is")
        return

    # Svara callback strax (fjarlægja „hleður..." á takka)
    bot.answer_callback_query(call.id, "Bý til greiðslulotu...")

    # Sækja plan upplýsingar
    pakki = fa_plan_upplysingar(plan)
    if not pakki:
        bot.send_message(chat_id, "❌ Ógilt plan — reyndu aftur með /askrift")
        return

    # Búa til Straumur checkout lotu
    nidurstada = bua_til_checkout(chat_id, plan)

    if nidurstada.get("villa"):
        bot.send_message(chat_id, f"⚠️ Villa við greiðslu: {nidurstada['villa']}\n\nHafa samband: sigvaldi@fjarmalin.is")
        return

    # Senda greiðsluhlekk sem inline takki
    checkout_url = nidurstada.get("url", "")
    if checkout_url:
        texti = (f"✅ *Greiðslulota stofnuð*\n\n"
                 f"📦 Pakki: {pakki['nafn']}\n"
                 f"💰 Verð: {pakki['verd_isk']:,} kr/mán\n\n"
                 f"Smelltu á takkann til að ljúka greiðslu:")

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Greiða núna", url=checkout_url))

        try:
            bot.send_message(chat_id, texti, parse_mode="Markdown", reply_markup=markup)
        except:
            bot.send_message(chat_id, texti, reply_markup=markup)
    else:
        bot.send_message(chat_id, "⚠️ Gat ekki búið til greiðsluhlekk — reyndu aftur síðar.")


# =============================================================
# SKIPANIR — /askrift og /stada
# =============================================================

@bot.message_handler(commands=['askrift'])
def askrift_skipun(m):
    """Sýnir verðskrá og plan valmöguleika."""
    senda_greidslubod(m.chat.id)


@bot.message_handler(commands=['stada'])
def stada_skipun(m):
    """Sýnir stöðu notanda — premium/fríar prufur."""
    chat_id = m.chat.id

    if chat_id == MASTER_ID:
        bot.reply_to(m, "👑 Sigvaldi — ótakmarkaður aðgangur (Master)")
        return

    try:
        notandi = saekja_notanda(chat_id)
        if notandi and notandi.get("is_premium"):
            lokadagur = notandi.get("subscription_end", "Ótímabundið")
            plan = notandi.get("subscription_plan", "?")
            texti = (f"✅ *Premium notandi*\n"
                     f"📦 Pakki: {plan}\n"
                     f"📅 Gildir til: {lokadagur[:10] if lokadagur else 'Ótímabundið'}")
        else:
            frir = get_free_queries_left(chat_id)
            texti = (f"ℹ️ *Ókeypis aðgangur*\n"
                     f"📊 Fríar prufur eftir: {frir}/5\n\n"
                     f"Sláðu inn /askrift til að uppfæra í premium.")
        try:
            bot.reply_to(m, texti, parse_mode="Markdown")
        except:
            bot.reply_to(m, texti)
    except Exception as e:
        bot.reply_to(m, f"Villa: {str(e)[:100]}")


# =============================================================
# KJARNAFALL — óbreytt frá v9 (nema smávægilegar lagfæringar)
# =============================================================

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
        if VALIDATOR_VIRKUR:
            import re as _re
            _urls = _re.findall(r"https?://\S+", svar)
            if _urls:
                _mat = score_sources(_urls)
                if _mat["warning"]:
                    svar = svar + get_warning_text()
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


# =============================================================
# HANDLERS — text og skrár
# =============================================================

@bot.message_handler(commands=['start','help'])
def welcome(m):
    texti = ("🧠 *Mímir v9.1 DEV*\n\n"
             "Ég man eftir samtalinu og svara á íslensku.\n"
             "Sendu texta, skjöl, myndir, video eða raddskeyti.\n\n"
             "📋 *Skipanir:*\n"
             "/askrift — sjá áskriftarleiðir\n"
             "/stada — sjá stöðu þína\n"
             "/gleymdu — hreinsa minni")
    try:
        bot.reply_to(m, texti, parse_mode="Markdown")
    except:
        bot.reply_to(m, texti)

@bot.message_handler(commands=['gleymdu','reset'])
def gleymdu(m):
    with memory_lock: user_sessions[m.chat.id].clear()
    bot.reply_to(m,"Minni hreinsað!")

@bot.message_handler(content_types=['text'])
def handle_text(m):
    texti=m.text.strip()
    if texti.startswith('/'): return
    chat_id=m.chat.id
    leyfður,frir=athuga_adgang(chat_id)
    if not leyfður:
        senda_greidslubod(chat_id)
        return
    if SANITIZER_VIRKUR and not is_safe_prompt(texti):
        bot.reply_to(m, get_rejection_message())
        return
    sm=bot.reply_to(m,"Mímir hugsar...")
    def run():
        try:
            # Sprint 15.4 — V5 Supervisor tekur við ef virkur
            if V5_VIRKUR:
                bot.edit_message_text("🧠 Mímir V5 vinnur...",chat_id=chat_id,message_id=sm.message_id)
                svar=MIMIR_V5.process_message(texti, user_id=chat_id)
                flokkun="V5"
            else:
                # Fallback á v4 rökfræði
                flokkun=flokka_beidni(texti)
                if flokkun=="SEARCH":
                    bot.edit_message_text("Kveiki á Ratsjá...",chat_id=chat_id,message_id=sm.message_id)
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
    sm=bot.reply_to(m,"Móttekur skrá...")
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
            bot.edit_message_text("Greini skrá...",chat_id=chat_id,message_id=sm.message_id)
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


# =============================================================
# RÆSING
# =============================================================

if __name__=="__main__":
    setja_upp_gagnagrunn()
    print(f"Mímir v9.1 DEV (Straumur paywall) ræstur — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if STRAUMUR_VIRKUR:
        print("💳 Straumur paywall VIRKUR")
    else:
        print("⚠️  Straumur paywall ÓVIRKUR — fallback texti")
    # VORN GEGN 409 CONFLICT
    try:
        bot.remove_webhook()
        time.sleep(2)
        print("Webhook hreinsat — 409 vorn virk")
    except Exception as e:
        print(f"Webhook: {e}")
    bot.infinity_polling(skip_pending=True)

# ============================================================
# SPRINT 12 — Öryggi (bætt við v9 DEV)
# SPRINT 15.3 — Straumur paywall (inline takkar + /askrift)
# ============================================================
