from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
from pathlib import Path
import sys, os, time, json
from fpdf import FPDF

jandi_url = 'https://www.jandi.com/landing/kr/signin'
font_name = 'NanumBarunGothic'
font_path = font_name+ '.ttf'

print ('\njandi.exe started.\n')

workdir = os.getcwd() 
os.chdir (workdir)
load_dotenv ()

Usage = "\n" \
"Usage: \n\n" \
"1) copy 'env.sample' to '.env'\n" \
"2) modify '.env' file for your information (i.e. email, passwd, ignore keyword, headless or not, verbose)\n" \
"3) copy font-family 'NanumBarunGothic.ttf' to same folder\n" \
"4) run jandi.exe\n" \
"\n"

env_exist = os.path.exists (os.path.join (workdir, '.env'))
#if os.path.exists (os.path.join (workdir, '.env') != True):
if not env_exist:
    print (Usage) 
    sys.exit ()

email         = os.getenv ('EMAIL')
password      = os.getenv ('PASSWORD')
ignore_topics = os.getenv ('IGNORE_TOPICS').split(',')
ignore_chats  = os.getenv ('IGNORE_CHATS').split(',')
download      = os.path.join (workdir, "download")
output        = os.path.join (workdir, "output")

Path(download).mkdir (parents=True, exist_ok=True)
Path(output).mkdir   (parents=True, exist_ok=True)

if os.getenv ('HEADLESS') == 'true':
    headless = True
else:
    headless = False

if os.getenv ('VERBOSE') == 'true':
    verbose = True
else:
    verbose = False

NUM_PAGEUP  = int (os.getenv ('NUM_PAGEUP'))
MAX_RETRY   = int (os.getenv ('MAX_RETRY'))
SLEEP_MINOR = 0.1
SLEEP_MAJOR = 0.8

print ('Parameters')
print ('-------------------------------------------------------')
print ('EMAIL        :', email)
print ('IGNORE_TOPICS:', ignore_topics)
print ('IGNORE_CHATS :', ignore_chats)
print ('DOWNLOAD_DIR :', download)
print ('OUTPUT_DIR   :', output)
print ('NUM_PAGEUP   :', NUM_PAGEUP)
print ('MAX_RETRY    :', MAX_RETRY)
print ('HEADLESS     :', headless)
print ('VERBOSE      :', verbose)
print ('\n\n')

options = webdriver.ChromeOptions()
if headless == True:
    options.add_argument('headless')
else:
    options.add_argument('head')
options.add_argument("disable-gpu")   # 가속 사용 x
prefs = {"download.default_directory" : download, "profile.default_content_setting_values.automatic_downloads" : 1, "media.autoplay.enabled" : False}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options) 

def sortOnKeys (d):
    return sorted(d.items(), key=lambda x: x[0])

def pressPagUpKey (count = 5):
    actions = driver.find_element (By.TAG_NAME, "body")
    for i in range (0, count): 
        actions.send_keys (Keys.PAGE_UP)
        time.sleep (SLEEP_MINOR)

def unLink (f):
    try:
        os.unlink (f)
    except OSError:
        pass

def dict2json (f, d):
    with open(f, 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(d, indent=2, ensure_ascii=False))

def dict2text (f, d):
    with open(f, 'w', encoding='utf-8') as fp:
        for k, v in d:
            _type = v['type']
            _name = v['name']
            _time = v['time']
            _msg  = v['msg']

            if (_type == 'sys'):
                fp.write('[' + _msg + ']\n\n')
            else:
                fp.write(_name + ' (' + _time + ')\n' + _msg + '\n\n')

def dict2pdf (f, d):
    pdf = FPDF()
    pdf.add_font(font_name, '', os.path.join (os.getcwd(),font_path), uni=True)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font(font_name, '', 12)

    for k, v in d:
        _type = v['type']
        _name = v['name']
        _time = v['time']
        _msg  = v['msg']

        if (_type == 'sys'):
            pdf.write (10, '[' + _msg + ']\n')
        else:
            pdf.write (10, _name + ' (' + _time + ')\n' + _msg + '\n\n')

    unLink (f)
    pdf.output(f)

def topicRoomEnter (topicId, topicNm):
    _messages = {}
    driver.find_element (By.ID, topicId).click()

    retry = 0

    while retry < MAX_RETRY:
        if (retry > 0):
            time.sleep (SLEEP_MAJOR)
            
        messages = driver.find_elements (By.CLASS_NAME, "_message.present")
        messageN = len (messages)

        prev = ""
        for i in range(0, len (messages)):
            id = messages[i].get_attribute("id");
            if (id == ''):
                id = messages[i].find_element (By.CLASS_NAME, "_systemMsgDate").get_attribute ("data-id")
                id =  int(id) * 10
            else:
                id = int(id) * 10 + 1

            if (id in _messages):
                continue

            retry   = 0
            updated = True

            _sys = False
            _msg  = ''
            _time = ''
            _name = ''

            try:
                _msg  = messages[i].find_element (By.CLASS_NAME, "msg-item").text
            except: 
                try:
                    _msg  = messages[i].find_element (By.CLASS_NAME, "info-title").text
                except: 
                    _sys = True

            if (_sys):
                _msg = messages[i].find_element (By.CLASS_NAME, "msg-system").text
                _messages[id] = { 'type': 'sys', 'name': '', 'time': '', 'msg': _msg }
                continue
            
            try:
                _name = messages[i].find_element (By.CLASS_NAME, "member-names").text
            except:
                _name = prev
            
            try:
                _time = messages[i].find_element (By.CLASS_NAME, "fn-time-stamp").get_attribute("tooltip")
            except:
                pass

            if verbose:
                print (_name, _time, _msg)

            files = messages[i].find_elements (By.CLASS_NAME, "file-type-wrap")
            for j in range (0, len (files)):
                file = files[j].find_element (By.CLASS_NAME, "info-title").text
                dir = os.path.join (download, file)
                
                unLink (dir)
                                
                downloadBtn = files[j].find_element (By.CLASS_NAME, "ui-icon.icon-ic-download")
                driver.execute_script("arguments[0].click();", downloadBtn);
            
            prev = _name; 
            _messages[id] = { 'type': 'msg', 'name': _name, 'time': _time, 'msg': _msg};
        
        pressPagUpKey (NUM_PAGEUP);  
        retry += 1    
    
    _messages = sortOnKeys(_messages);
    
    dict2json (os.path.join (output, topicNm + '.json'), _messages)
    dict2text (os.path.join (output, topicNm + '.txt' ), _messages)
    dict2pdf  (os.path.join (output, topicNm + '.pdf' ), _messages)

    time.sleep (SLEEP_MAJOR)
 
def topicRoom ():
    resultRooms  = driver.find_elements (By.CLASS_NAME, "_topicItem")
    ncount = len (resultRooms)

    if verbose:
        print ('Number of topic room: ', ncount)

    for i in range (0, ncount): 
        resultRooms  = driver.find_elements (By.CLASS_NAME, "_topicItem"); # re-init 'StaleElementReferenceError'

        topicId = resultRooms[i].get_attribute ("id")
        topicNm = resultRooms[i].find_element (By.CLASS_NAME, "lnb-item-name").text
        ignore = False
        for j in range (0, len (ignore_topics)):
            if (topicNm.find (ignore_topics[j].strip ()) >= 0): 
                ignore = True
        
        if ignore == False:
            if verbose:
                print ('Enter topic-room: ' + topicNm + '(' + topicId +')')
            topicRoomEnter (topicId, topicNm)

def dmRoom ():
    resultRooms  = driver.find_elements (By.CLASS_NAME, "_dmItem")
    ncount = len (resultRooms)

    if verbose:
        print ('Number of DM room: ', ncount)

    for i in range (0, ncount): 
        resultRooms  = driver.find_elements (By.CLASS_NAME, "_dmItem"); # re-init 'StaleElementReferenceError'

        topicId = resultRooms[i].get_attribute ("id")
        topicNm = resultRooms[i].find_element (By.CLASS_NAME, "member-names").text
        ignore = False
        for j in range (0, len (ignore_chats)):
            if (topicNm.find (ignore_chats[j].strip ()) >= 0): 
                ignore = True
        
        if ignore == False:
            if verbose:
                print ('Enter dm-room: ' + topicNm + '(' + topicId +')')
            topicRoomEnter (topicId, topicNm)

def jandi ():
    if verbose:
        print ('WebDriver navigation: ' + jandi_url)

    driver.get(jandi_url)

    if verbose:
        print ('Login with ' + email)

    usernameField = driver.find_element(By.XPATH,'//*[@id="__next"]/div/main/div[1]/div/form/fieldset[1]/div[1]/input')
    passwordField = driver.find_element(By.XPATH, '//*[@id="__next"]/div/main/div[1]/div/form/fieldset[1]/div[2]/input')
    loginButton   = driver.find_element(By.CSS_SELECTOR, '#__next > div > main > div.Signin_signinWrap__21AXo > div > form > button')

    usernameField.send_keys (email)
    passwordField.send_keys (password)
    loginButton.click ()

    WebDriverWait (driver, 20).until (EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/article/div/section[2]/article/ul/li/div/button[2]/span/span')))

    if verbose:
        print ('Login completed.')

    joinButton   =  driver.find_element (By.XPATH, '//*[@id="wrap"]/article/div/section[2]/article/ul/li/div/button[2]/span/span')
    joinButton.click ()

    WebDriverWait (driver, 20).until (EC.presence_of_element_located((By.XPATH, '//*[@id="jndApp"]/div[1]/div[2]/div[1]/div[1]/div/div[1]/div/div[1]/div[1]/div[2]/div[1]/span')))

    if verbose:
        print ('Enter JANDI main-page')

    topicRoom ()
    dmRoom ()

jandi ()

print ('\nCompleted.\n\n')