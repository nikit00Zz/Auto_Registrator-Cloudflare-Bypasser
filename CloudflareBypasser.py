import time
from DrissionPage import ChromiumPage

class CloudflareBypasser:
    def __init__(self, driver: ChromiumPage, max_retries=-1, log=True):
        self.driver = driver
        self.max_retries = max_retries
        self.log = log

    def search_recursively_shadow_root_with_iframe(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.child().tag == "iframe":
                return ele.shadow_root.child()
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_iframe(child)
                if result:
                    return result
        return None

    def search_recursively_shadow_root_with_cf_input(self,ele):
        if ele.shadow_root:
            if ele.shadow_root.ele("tag:input"):
                return ele.shadow_root.ele("tag:input")
            
        else:
            for child in ele.children():
                result = self.search_recursively_shadow_root_with_cf_input(child)
                if result:
                    return result
                    
                
        return None
    
    def locate_cf_button(self):
        button = None
        eles = self.driver.eles("tag:input")
        for ele in eles:
            if "name" in ele.attrs.keys() and "type" in ele.attrs.keys():
                if "cf_challenge_response" in ele.attrs["name"] and ele.attrs["type"] == "hidden":
                    button = ele.parent().shadow_root.child()("tag:body").shadow_root("tag:input")
                    break
            
        if button:
            return button
        else:
            
            self.log_message("Базовый поиск неудался. Ищем кнопку рекурсией.")
            ele = self.driver.ele("tag:body")
            iframe = self.search_recursively_shadow_root_with_iframe(ele)
            if iframe:
                button = self.search_recursively_shadow_root_with_cf_input(iframe("tag:body"))
            else:
                self.log_message("Iframe не найден. Кнопка не найдена.")
            return button

    def log_message(self, message):
        if self.log:
            print(message)             

    def click_verification_button(self):
        try:
            button = self.locate_cf_button()
            if button:
                self.log_message("Кнопка найдена. Пробуем нажать.")
                button.click()
            else:
                self.log_message("Кнопка не доступна.")

        except Exception as e:
            self.log_message(f"Ошибка: {e}")

    def is_bypassed(self):
        try:
            title = self.driver.title.lower()
            return "один момент" not in title
        except Exception as e:
            self.log_message(f"Ошибка проверки страницы title: {e}")
            return False

    def bypass(self):
        
        try_count = 0

        while not self.is_bypassed():
            if 0 < self.max_retries + 1 <= try_count:
                break

            self.log_message(f"Attempt {try_count + 1}: Страница найдена. Пытаемся обойти...")
            self.click_verification_button()

            try_count += 1
            time.sleep(2)

        if self.is_bypassed():
            self.log_message("Готово.")
        else:
            self.log_message("Неудалось обойти.")
