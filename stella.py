import os
import random
import time
import signal
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome, ChromeOptions

class WhatsAppStatusAutomator:
    def __init__(self):
        self.driver = None
        self.running = True
        self.setup_interrupt_handler()
        self.setup_driver()

    def setup_interrupt_handler(self):
        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

    def setup_driver(self):
        options = ChromeOptions()
        #options.add_argument(f"--user-data-dir={os.path.expanduser('~')}/.config/chromium")  # Ajuste para seu OS
        userdir = '/home/xan/Documents/sessions-selenium/stella/1'
        options.add_argument(f"--user-data-dir={userdir}")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        
        self.driver = Chrome(options=options)
        self.driver.set_window_size(1280, 720)

    def random_delay(self, min_sec=1, max_sec=5):
        time.sleep(random.uniform(min_sec, max_sec))

    def navigate_to_status(self):
        try:
            # Localizar e clicar na aba de Status
            status_button_xpath = '/html/body/div[1]/div/div/div[3]/div/header/div/div/div/div/span/div/div[1]/div[2]/button'
            WebDriverWait(self.driver, 300).until(
                EC.element_to_be_clickable((By.XPATH, status_button_xpath))
            ).click()
            self.random_delay(2, 4)
            return True
        except Exception as e:
            print(f"Erro ao acessar Status: {str(e)}")
            return False

    def view_status_updates(self):
        try:
            # Localizar todos os status disponíveis
            status_items_xpath = '//div[@data-testid="status-item"]'
            statuses = WebDriverWait(self.driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, status_items_xpath))
            )

            for index, status in enumerate(statuses):
                if not self.running:
                    break
                
                # Clicar no status
                status.click()
                self.random_delay(3, 7)
                
                # Interagir com o status (exemplo: visualizar até o fim)
                self.watch_full_status()
                
                # Voltar para lista de status
                self.driver.back()
                self.random_delay(2, 3)

            return True
        except Exception as e:
            print(f"Erro ao visualizar status: {str(e)}")
            return False

    def watch_full_status(self):
        try:
            # Esperar o player de status carregar
            player_xpath = '//div[@role="main" and @aria-label="Player de status"]'
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, player_xpath))
            )

            # Avançar status automaticamente
            while self.running:
                next_button_xpath = '//div[@aria-label="Próximo"]'
                next_button = self.driver.find_elements(By.XPATH, next_button_xpath)
                
                if next_button:
                    next_button[0].click()
                    self.random_delay(5, 8)  # Tempo médio de um status
                else:
                    break

        except Exception as e:
            print(f"Erro durante reprodução: {str(e)}")

    def post_text_status(self, text):
        try:
            # Abrir criação de novo status
            new_status_button_xpath = '//div[@aria-label="Novo status"]'
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, new_status_button_xpath))
            ).click()

            # Selecionar opção de texto
            text_option_xpath = '//div[@aria-label="Status de texto"]'
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, text_option_xpath))
            ).click()

            # Inserir texto
            text_area_xpath = '//div[@role="textbox"]'
            text_area = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, text_area_xpath))
            )
            text_area.send_keys(text)
            self.random_delay(1, 2)

            # Publicar
            send_button_xpath = '//div[@aria-label="Enviar"]'
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, send_button_xpath))
            ).click()

            return True
        except Exception as e:
            print(f"Erro ao postar status: {str(e)}")
            return False

    def graceful_shutdown(self, signum=None, frame=None):
        print("\nFinalizando operações...")
        self.running = False
        if self.driver:
            self.driver.quit()
        sys.exit(0)

    def run(self):
        try:
            self.driver.get("https://web.whatsapp.com")
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.ID, "app"))
            )

            if self.navigate_to_status():
                # Exemplo de fluxo:
                # 1. Visualizar status existentes
                self.view_status_updates()
                
                # 2. Postar novo status de texto
                self.post_text_status("Automação de status funcionando! 🤖")
                
                # Manter aberto para demonstração
                input("Pressione Enter para finalizar...")

        finally:
            self.graceful_shutdown()

if __name__ == "__main__":
    automator = WhatsAppStatusAutomator()
    automator.run()