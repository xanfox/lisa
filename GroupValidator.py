import os
import random
import time
import signal
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from undetected_chromedriver import Chrome, ChromeOptions

class GroupValidator:
    def __init__(self, input_file="links.txt", valid_file="ativos.txt", invalid_file="blacklist.txt"):
        self.input_file = input_file
        self.valid_file = valid_file
        self.invalid_file = invalid_file
        self.processed_urls = set()
        self.driver = None
        self.current_index = 0
        
        # Configurar tratamento de interrupção
        signal.signal(signal.SIGINT, self.handle_interrupt)
        
        # Carregar progresso anterior
        self.load_progress()

    def setup_driver(self):
        options = ChromeOptions()
        #options.add_argument("--headless=new")  # Remova para ver o navegador
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = Chrome(options=options)

    def load_progress(self):
        # Carregar URLs já processados
        for file in [self.valid_file, self.invalid_file]:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    self.processed_urls.update(line.strip() for line in f)

    def save_progress(self):
        # Salvar estado atual para continuar depois
        with open("state.txt", 'w') as f:
            f.write(str(self.current_index))

    def handle_interrupt(self, signum, frame):
        print("\nInterrupção detectada. Salvando estado...")
        self.save_progress()
        if self.driver:
            self.driver.quit()
        sys.exit(0)

    def validate_group(self, url):
        try:
            self.driver.get(url)
            
            
            
            
            # # Esperar carregamento inicial
            # WebDriverWait(self.driver, 3).until(
            #     EC.presence_of_element_located((By.XPATH, '//div[@id="app"]'))
            # )

            # Verificar elemento h3 de validação
            try:

                el = self.driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/div[2]/div/section/div/div/div/div/div[2]/h3").text
                if el != "":
                    return True
            except:
                return False

        except Exception as e:
            print(f"Erro ao validar {url}: {str(e)}")
            return False

    def process_urls(self):
        with open(self.input_file, 'r') as f:
            all_urls = [line.strip() for line in f if line.strip()]

        # Continuar de onde parou
        if os.path.exists("state.txt"):
            with open("state.txt", 'r') as f:
                self.current_index = int(f.read())

        self.setup_driver()

        try:
            for i in range(self.current_index, len(all_urls)):
                url = all_urls[i]
                self.current_index = i
                
                if url in self.processed_urls:
                    continue

                # Intervalo aleatório entre 5-15 segundos
                delay = random.uniform(3, 7)
                print(f"Aguardando {delay:.2f} segundos antes da próxima verificação...")
                time.sleep(delay)

                if self.validate_group(url):
                    with open(self.valid_file, 'a') as f:
                        f.write(f"{url}\n")
                    print(f"VÁLIDO: {url}")
                else:
                    with open(self.invalid_file, 'a') as f:
                        f.write(f"{url}\n")
                    print(f"INVÁLIDO: {url}")

                # Atualizar conjunto de processados
                self.processed_urls.add(url)

                # Salvar estado a cada 10 iterações
                if i % 10 == 0:
                    self.save_progress()

        finally:
            self.save_progress()
            self.driver.quit()
            os.remove("state.txt") if os.path.exists("state.txt") else None

if __name__ == "__main__":
    validator = GroupValidator(
        input_file="lista_grupos.txt",
        valid_file="grupos_ativos.txt",
        invalid_file="blacklist.txt"
    )
    
    validator.process_urls()