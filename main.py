import os
import random
import time
import subprocess
import pyautogui
import pyperclip
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pprint import pprint


class WhatsCliker:
    def __init__(self, driver, scroll_increment=300, sleep_time=0.5):
        self.driver = driver
        self.scroll_increment = scroll_increment
        self.sleep_time = sleep_time
        self.captured_chats = set()
        self.folder_path = "./copys"

    def acessar_whatsapp(self):
        self.driver.set_window_size(960, 1080)  # Define o tamanho
        self.driver.set_window_position(0, 0)  # Define a posição
        self.driver.get("https://web.whatsapp.com")
        print("Aguarde enquanto verificamos se a sessão foi carregada...")
        try:
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
            print("Login realizado com sucesso e sessão carregada!")
        except Exception as e:
            print("Erro ao carregar a sessão ou encontrar o elemento:", e)
            traceback.print_exc()
            self.driver.quit()

    def scroll_and_capture(self):
        """
        Realiza scroll para baixo até o final e volta ao topo,
        capturando os chats e enumerando-os. Para ao pressionar Enter.
        """
        try:
            pane_side = self.driver.find_element(By.ID, "pane-side")
        except Exception as e:
            print(f"Erro ao localizar o painel de chats: {e}")
            return

        print("Iniciando scroll... Pressione Enter para parar.")
        try:
            while True:
                # Scroll para baixo até o final
                while True:
                    chats = pane_side.find_elements(By.XPATH, './/*[@role="listitem"]')
                    for chat in chats:
                        try:
                            title_element = chat.find_element(By.XPATH, './/span[@title]')
                            title = title_element.get_attribute("title")
                            if title and title not in self.captured_chats:
                                self.captured_chats.add(title)
                                print(f"{len(self.captured_chats)}. {title}")
                        except Exception:
                            continue

                    # Scroll para baixo
                    previous_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollTop += arguments[1];",
                        pane_side,
                        self.scroll_increment,
                    )
                    time.sleep(self.sleep_time)

                    # Verifica se chegou ao final
                    current_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    if current_scroll == previous_scroll:
                        break

                # Volta ao topo
                while True:
                    previous_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollTop -= arguments[1];",
                        pane_side,
                        self.scroll_increment,
                    )
                    time.sleep(self.sleep_time)

                    # Verifica se chegou ao topo
                    if previous_scroll == 0:
                        break

                # Verifica input do usuário para parar
                if self._stop_requested():
                    print("\nScroll interrompido pelo usuário.")
                    break

        except Exception as e:
            print(f"Erro durante scroll: {e}")

        print("\nProcesso finalizado. Total de chats capturados:")
        for idx, chat in enumerate(self.captured_chats, start=1):
            print(f"{idx}. {chat}")

    def _stop_requested(self):
        """
        Verifica se o usuário pressionou Enter no terminal para interromper o loop.
        """
        import sys
        import select

        i, _, _ = select.select([sys.stdin], [], [], 0)
        if i:
            sys.stdin.readline()  # Limpa o buffer
            return True
        return False

    def save_chats_to_file(self, filename=None):      
        #Salva os chats capturados em um arquivo .txt. 
        # :param filename: Nome do arquivo para salvar (opcional).
        # Se não fornecido, será usado um nome padrão.   
        if not self.captured_chats:
            print("Nenhum chat capturado para salvar.")
            return

        # Solicita o nome do arquivo ao usuário, com um padrão
        if not filename:
            filename = input("Digite o nome do arquivo para salvar os chats (padrão: 'captured_chats.txt'): ").strip()
            if not filename:
                filename = "captured_chats.txt"

        # Salva os chats no arquivo
        try:
            with open(filename, "w", encoding="utf-8") as file:
                for idx, chat in enumerate(sorted(self.captured_chats), start=1):
                    file.write(f"{chat}\n")
            print(f"Chats capturados salvos com sucesso em: {filename}")
        except Exception as e:
            print(f"Erro ao salvar os chats em arquivo: {e}")


    def load_chats_from_file(self, filename="captured_chats.txt"):
        """
        Recupera os chats salvos em um arquivo .txt e armazena em um conjunto.

        :param filename: Nome do arquivo .txt contendo os chats capturados (padrão: "captured_chats.txt")
        :return: Conjunto de chats recuperados do arquivo.
        """
        if not os.path.exists(filename):
            print(f"Arquivo {filename} não encontrado.")
            return set()

        with open(filename, "r", encoding="utf-8") as file:
            retrieved_chats = {line.strip() for line in file if line.strip()}  # Remove linhas vazias e duplica

        # Armazena no atributo da classe
        self.retrieved_chats_from_file = retrieved_chats

        # Exibe os chats recuperados
        print("Chats recuperados do arquivo:")
        for idx, chat in enumerate(retrieved_chats, start=1):
            print(f"{idx}. {chat}")

        return retrieved_chats


    def filter_chats_to_exclusion_file(self, chats, exclusion_file="exclusion_file.txt"):
        """
        Itera sobre uma lista de chats e pergunta ao usuário se deseja adicionar cada chat a um arquivo de exclusão.

        :param chats: Lista de chats a serem iterados
        :param exclusion_file: Nome do arquivo de exclusão
        """
        try:
            with open(exclusion_file, "a", encoding="utf-8") as file:
                for chat in chats:
                    resposta = input(f"Deseja adicionar '{chat}' ao arquivo de exclusão? [y para sim, Enter para não]: ").strip().lower()
                    if resposta == "y":
                        file.write(chat + "\n")
                        print(f"'{chat}' adicionado ao arquivo de exclusão.")
                    else:
                        print(f"'{chat}' ignorado.")
            print(f"Processo de exclusão concluído. Chats salvos em {exclusion_file}.")
        except Exception as e:
            print(f"Erro ao processar os chats para exclusão: {e}")


    def scroll_and_find(self, target_chats, exclusion_zone):
        """
        Realiza scroll para baixo até localizar todos os chats no conjunto `target_chats`,
        deixando-os disponíveis para clique. Volta ao topo ao final.

        :param target_chats: Conjunto de nomes de chats a serem localizados.
        :param exclusion_zone: Chats que serão ignorados
        """


        try:
            pane_side = self.driver.find_element(By.ID, "pane-side")
        except Exception as e:
            print(f"Erro ao localizar o painel de chats: {e}")
            return

        found_chats = set()
        counter_1 = 0
        
        try:
            # vamos forçar o encerramento por enquanto
            while (target_chats - found_chats - exclusion_zone) and (counter_1 < 7):  # Enquanto houver chats a encontrar
                counter_1 = counter_1 + 1
                print("#######| BUNKER |###########| BUNKER |###########| BUNKER |############")
                print(f"While externo: rodada {counter_1}")
                print(f"Total in target: {len(target_chats - exclusion_zone)}")
                print(f"Total in found: {len(found_chats)}")
                pprint(target_chats - found_chats)
                print("#######| RESULT |###########| RESULT |###########| RESULT |############")

                # Scroll para baixo até o final
                while target_chats - found_chats - exclusion_zone:
                    chats = pane_side.find_elements(By.XPATH, './/*[@role="listitem"]')
                    for chat in chats:
                        try:
                            title_element = chat.find_element(By.XPATH, './/span[@title]')
                            title = title_element.get_attribute("title")
                            print(f"### | TENTANDO:{title}")
                            if title and title in target_chats and title not in found_chats and title not in exclusion_zone:
                                
                                chat_toclick = self.driver.find_element(By.XPATH, f'//*[@title="{title}"]')
                                chat_toclick.click()
                                
                                
                                ###############################################################
                                ################## | VAMOS APAGAR OS CHATS ANTES |############# 
                                ###############################################################
                                # localizar botões mais opções



                                # Clicar

                                try:
                                    WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, '//div[@id="main"]//button[@aria-label="Mais opções" and @title="Mais opções"]'))
                                    ).click()
                                    print("*** Clicou no Botão mais Opções com Sucesso!***")
                                except Exception as e:
                                    print(f"Erro ao clicar no botão mais opções: {e}")

                                try:
                                    WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Limpar conversa" and text()="Limpar conversa"]'))
                                    ).click()
                                    print("+++ Clicou no Botão Limpar Conversa +++")
                                except Exception as e:
                                    print(f"Erro ao clicar no botão limpar conversa: {e}")

                                try:
                                    WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, '//button[.//div[contains(text(), "Limpar conversa")]]'))
                                    ).click()
                                    print("$$$ Clicou no Botão Limpar Conversa interno $$$")
                                except Exception as e:
                                    print(f"Erro ao clicar no botão limpar conversa interno, mensagens não apagadas: {e}")



                                time.sleep(3)
                                ######################### | BIG MOMENT | ###########################################
                                                # Seleção de arquivo aleatório e envio de mensagem
                                try:
                                    random_file = self._get_random_txt_file()
                                    file_path = os.path.join(self.folder_path, random_file)
                                    with open(file_path, "r", encoding="utf-8") as file:
                                        content = file.read().strip()
                                        pyperclip.copy(content)

                                    if content:
                                        message_box = self.driver.switch_to.active_element
                                        message_box.send_keys(Keys.CONTROL, "a")
                                        message_box.send_keys(Keys.CONTROL, Keys.DELETE)
                                        message_box.send_keys(Keys.CONTROL, "v")

                                        # Chamar a função para clicar no botão de anexo
                                        self.click_attach_button()
                                        # Clica no botão anexar imagem
                                        self.click_photo_attach_button()
                                    else:
                                        print(f"O arquivo selecionado ({random_file}) está vazio.")
                                except FileNotFoundError as e:
                                    print(e)

                    
                                
                                delay = random.uniform(9, 35)
                                print(f"Aguardando {delay:.2f} segundos antes do próximo clique.")  # Log do delay
                                time.sleep(delay)  # Pausa antes do clique
                                
                                found_chats.add(title)
                                print(f"Chat encontrado: {title}")
                                # Opcional: Rolagem para trazer o chat completamente visível
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView(true);", chat
                                )
                                time.sleep(self.sleep_time)  # Pode ajustar o tempo conforme necessário
                        except Exception:
                            continue

                    # Scroll para baixo
                    previous_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollTop += arguments[1];",
                        pane_side,
                        self.scroll_increment,
                    )
                    time.sleep(self.sleep_time)

                    # Verifica se chegou ao final
                    current_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    if current_scroll == previous_scroll:
                        break

                # Volta ao topo
                while target_chats - found_chats:
                    previous_scroll = self.driver.execute_script(
                        "return arguments[0].scrollTop;", pane_side
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollTop -= arguments[1];",
                        pane_side,
                        self.scroll_increment,
                    )
                    time.sleep(self.sleep_time)

                    # Verifica se chegou ao topo
                    if previous_scroll == 0:
                        break

        except Exception as e:
            print(f"Erro durante a busca: {e}")

        print("\nProcesso de busca finalizado.")
        if found_chats:
            print("Chats encontrados:")
            for chat in found_chats:
                print(f"- {chat}")
        else:
            print("Nenhum dos chats especificados foi encontrado.")

        return found_chats

    def _get_random_txt_file(self):
        """Valida a pasta e retorna um arquivo de texto aleatório."""
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"Pasta '{self.folder_path}' não encontrada.")
        txt_files = [f for f in os.listdir(self.folder_path) if f.endswith(".txt")]
        if not txt_files:
            raise FileNotFoundError("Nenhum arquivo .txt encontrado na pasta.")
        return random.choice(txt_files)

    def click_attach_button(self):
        """Clica no botão de anexar com espera dinâmica."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/div[3]/div/div[4]/div/footer/div[1]/div/span/div/div[1]/div/button/span"))
            ).click()
            print("Botão de anexar clicado com sucesso.")
        except Exception as e:
            print(f"Erro ao clicar no botão de anexar: {e}")


    def click_photo_attach_button(self):  # <-- CORRIJA A INDENTAÇÃO AQUI
        try:
            # Após clicar, interagir com a caixa de diálogo
            self.handle_file_dialog()
            input_file = self.driver.find_element(
                By.XPATH, 
                '//input[@type="file" and @accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
            )
            file_path = os.path.abspath("./change-img/output/nova_foto.jpg")
            input_file.send_keys(file_path)
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@role="button" and @aria-label="Enviar"]'))
            ).click()
        except Exception as e:
            print(f"Erro no upload: {e}")
            traceback.print_exc()

    def handle_file_dialog(self):  # <-- CORRIJA A INDENTAÇÃO AQUI
        try:
            bash_script_path = "./change-img/change-image.sh"
            subprocess.Popen(['bash', bash_script_path])
        except Exception as e:
            print(f"Erro ao chamar o script Bash: {e}")

 
    def execute_function_prompt(self, function):
        """
        Pergunta ao usuário se deseja executar a função passada como argumento.

        :param function: Função ou método a ser executado.
        """
        if hasattr(function, "__self__"):
            # Trata métodos de instância
            func_name = f"{function.__self__.__class__.__name__}.{function.__name__}"
        elif callable(function):
            # Trata funções independentes
            func_name = function.__name__
        else:
            raise ValueError("O argumento fornecido não é uma função válida.")

        resposta = input(f"Deseja executar {func_name}? [y/s para sim, Enter para não]: ").strip().lower()
        if resposta in ["y", "s"]:
            print(f"Executando {func_name}...")
            function()
        else:
            print(f"{func_name} não será executada.")




def main():

    start_time = time.time()

    # Configuração do driver
    options = uc.ChromeOptions()
        
    userdir = '/home/xan/Documents/sessions-selenium/one'
    options.add_argument(f"--user-data-dir={userdir}")
    # options.add_argument("--headless=new")  # Modo headless moderno (Chrome 112+)
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")  # Resolução fixa
    # options.add_argument("--disable-blink-features=AutomationControlled")  # Oculta automação

    # Adicione um user-agent realista
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)
    
    
    WC = WhatsCliker(driver)
    WC.acessar_whatsapp()

  
    # Perguntar ao usuário se deseja executar scroll_and_capture
    WC.execute_function_prompt(WC.scroll_and_capture)
    # Perguntar ao usuário se deseja exportar chats capturados para txt
    WC.execute_function_prompt(WC.save_chats_to_file)
    # Carrega os chats do arquivo txt
    chats = WC.load_chats_from_file()
    # Filtra os chats carregados
    WC.execute_function_prompt(lambda: WC.filter_chats_to_exclusion_file(chats))
    
    load_chats_from_exclusion_zone = WC.load_chats_from_file("exclusion_file.txt")
    WC.scroll_and_find(chats, load_chats_from_exclusion_zone)

    # Calcula o tempo total de execução
    elapsed_time = (time.time() - start_time) / 60
    print(f"Tempo total de execução: {elapsed_time:.2f} minutos")    
    
    print("#############################################################################################")
    print("##################################|ATÉ AQUI TUDO BEM |#######################################")
    print("#############################################################################################")
    time_to_sleeep = input('Vai dormir quanto tempo?') or 15
    print(f"Vai Dormir: {time_to_sleeep} segundos")
    time.sleep(int(time_to_sleeep))


    driver.quit()


if __name__ == "__main__":
    main()
