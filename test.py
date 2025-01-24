import time
import logging
import os
import requests
import re
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# API временной почты для прохождения подтверждения по email
API = 'https://www.1secmail.com/api/v1/'
acc_number = 0

# Конфигурация логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloudflare_bypass.log', mode='w')
    ]
)

# Опции браузера.
def get_chromium_options(browser_path: str, arguments: list) -> ChromiumOptions:

    options = ChromiumOptions()
    options.set_argument('--auto-open-devtools-for-tabs', 'true')
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    return options

# Функция будет проверять email на входящие сообщения
def check_mail(email = ''):
          
    r_link = f'{API}+?action=getMessages&login={email.split("@")[0]}&domain={email.split("@")[1]}'
    r = requests.get(r_link).json()
    length = len(r)
    if length == 0:
        pass
    else:
        id_list = []
        for i in r:
            for k, v in i.items():
                if k == 'id':
                    id_list.append(v)          
        for id in id_list:
            r_link = f'{API}+?action=readMessage&login={email.split("@")[0]}&domain={email.split("@")[1]}&id={id}'
            r = requests.get(r_link).json()
            textBody = r.get('textBody')
            with open ("msg.txt", 'w') as msg_link:
                    msg_link.write(textBody)
        return False

def main():
    global acc_number

    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    if isHeadless:
        from pyvirtualdisplay import Display

        display = Display(visible=0, size=(1920, 1080))
        display.start()

    browser_path = os.getenv('CHROME_PATH', "/usr/bin/google-chrome")

    arguments = [
        "-no-first-run",
        "-force-color-profile=srgb",
        "-metrics-recording-only",
        "-password-store=basic",
        "-use-mock-keychain",
        "-export-tagged-pdf",
        "-no-default-browser-check",
        "-disable-background-mode",
        "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
        "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
        "-deny-permission-prompts",
        "-disable-gpu",
        "-accept-lang=en-US",
    ]

    options = get_chromium_options(browser_path, arguments)

    driver = ChromiumPage(addr_or_opts=options)
    
    # acc_number уменьшается только в том случаи, когда акк полностью верифицирован, получен и записан ключ.
    # если возникают ошибки, требуемое количество пользователей остаётся прежним, и регистрация начинается с начала
    while acc_number != 0:
        try:
            driver.clear_cache()
            # Получаем случайные данные для регистрации ( password )
            data = requests.get("https://randomuser.me/api/?password=special,upper,lower,number,10-16").json()
            password = data['results'][0]['login']['password']
            password += "1"
            email = data['results'][0]['email']
    
            # Создаём случайный email на сервисе с временной почтой ( сервис сейчас не доступен )
            #email = requests.get('https://www.1secmail.com/api/v1/?action=genRandomMailbox').text
            #email = re.sub(r"\[\"|\"\]","",email)



            logging.info('Открыта страница регестрации.')
            driver.get('https://dash.cloudflare.com/sign-up')
            
            # Используем задержки
            time.sleep(20)

            # Проверяем, если по каким то причинам не разлогинились.
            if driver('@class:c_er c_es').text == 'Get started with Cloudflare':
                pass
            else:
                # Делаем Logout.
                driver.ele('@data-testid:user-selector-dropdown-button').click()

                time.sleep(5)
            
                driver.ele('@data-testid:user-selector-link-logout').click()

                time.sleep(5)

                driver.get('https://dash.cloudflare.com/sign-up')

                time.sleep(20)
        
        
            logging.info('Обходим каптчу.')
            cf_bypasser = CloudflareBypasser(driver)
            cf_bypasser.click_verification_button() 

            # Вводим ранее сгенерированные данные
            driver.ele('@name:email').input(email)
            driver.ele('@name:password').input(password)

            time.sleep(5)

            # Нажимаем кнопку Signup
            driver.ele('@type:submit').click()

            time.sleep(25)

            # В случае если потребовали ввести ещё раз каптчу
            if driver('@class:c_er c_es') == True and driver('@class:c_er c_es').text == 'Get started with Cloudflare':
                logging.info('Обходим каптчу ещё раз.')
                cf_bypasser = CloudflareBypasser(driver)
                cf_bypasser.click_verification_button() 
                time.sleep(5)
                # Нажимаем кнопку Signup
                driver.ele('@type:submit').click()
                time.sleep(25)

            # Запускаем цикл для проверки почты с переодичностью 5 сек.
            while check_mail(email):
                time.sleep(5)   

            logging.info('Сообщение с подтверждением принято.')
            with open("msg.txt",'r+') as msg_verf:
                lines = msg_verf.readlines()
                for line in lines:
                    if re.search(r"verification", line):
                        link = line        
                msg_verf.truncate(0)

            # Подтверждаем email.
            driver.get(link)

            time.sleep(15)

            # Получаем токен.
            driver.get('https://dash.cloudflare.com/profile/api-tokens')

            time.sleep(7)

            driver.ele('@data-testid:view-api-key-btn').click()

            time.sleep(7)    

            driver.ele('@name:password').input(password)
        
            time.sleep(7)

            cf_bypasser.click_verification_button() 
        
            time.sleep(5)

            driver.ele('@data-testid:confirm-password-modal-confirm-btn').click()

            time.sleep(5)

            text = driver('@name:api_key').text

            # Сохраняем полученные данные в файл.
            with open('auth_data.txt','a') as res_auth:
                res_auth.write(f'email: {email}\npassword: {password}\nAPI_KEY: {text}\n\n')

            # Делаем Logout.
            driver.get('https://dash.cloudflare.com/profile/api-tokens')

            time.sleep(10)

            driver.ele('@data-testid:user-selector-dropdown-button').click()

            time.sleep(5)

            driver.ele('@data-testid:user-selector-link-logout').click()

            time.sleep(5)

            logging.info("Аккаунт зарегестрирован.")

            acc_number -= 1
    
            time.sleep(15)
           
        except Exception as e:
            # Если что то пошло не так выдаёт ошибку и начинаем с начала.
            logging.error("Ошибка: %s", str(e))
            driver.get('https://dash.cloudflare.com/sign-up')

    driver.quit()    

if __name__ == '__main__':
    while True:
        try:
            acc_number = int(input("Введите количество аккаунтов: "))
        except Exception as e:
            print(f'Ошибка: {str(e)}') 
            continue
        else:
            main()
            break
    
