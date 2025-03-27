import os
import random
import time
import subprocess
import traceback
import json
import pyperclip
import shutil
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException


# ====================================================
# Configuração e Setup
# ====================================================

DEFAULT_CONFIG = {
    "user_data_dir": "/home/xan/Documents/sessions-selenium/one",
    "scroll_increment": 300,
    "sleep_time": 0.5,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "wait_timeout": 10,
    "exit_delay": 15,
    "execute_scroll_and_capture": True,
    "execute_save_chats_to_file": True,
    "execute_filter_chats": True,
    "monitor_user_data_dir": True,
    "user_data_dir_size_threshold_gb": 2,
    "copy_text_folder": "",
    "change_img_folder": "change-img",
    "captured_chats_file": "captured_chats.txt"   # Nova entrada para o arquivo de chats capturados
}

CONFIG_FILE = "config.json"

def load_config():
    """
    Tenta carregar o arquivo de configuração. Se não existir ou ocorrer erro,
    retorna as configurações padrão.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Erro ao ler o arquivo de configuração: {e}")
            print("Usando configurações padrão.")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """
    Salva as configurações no arquivo CONFIG_FILE.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"Configurações salvas em {CONFIG_FILE}.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo de configuração: {e}")

def setup_config():
    """
    Permite ao usuário configurar as opções do programa e salva em CONFIG_FILE.
    Pressione Enter para manter o valor atual.
    """
    config = load_config()
    print("===== Modo de Setup =====")
    print("Configure as opções abaixo (pressione Enter para manter o valor atual):")
    for key, value in config.items():
        # Tratamos 'copy_text_folder', 'change_img_folder' e 'captured_chats_file' separadamente
        if key in ["copy_text_folder", "change_img_folder", "captured_chats_file"]:
            continue
        new_value = input(f"{key} [{value}]: ").strip()
        if new_value:
            if isinstance(value, int):
                try:
                    config[key] = int(new_value)
                except:
                    print("Valor inválido, mantendo o valor anterior.")
            elif isinstance(value, float):
                try:
                    config[key] = float(new_value)
                except:
                    print("Valor inválido, mantendo o valor anterior.")
            elif isinstance(value, bool):
                lower_val = new_value.lower()
                if lower_val in ["true", "t", "y", "s", "1"]:
                    config[key] = True
                elif lower_val in ["false", "f", "n", "0"]:
                    config[key] = False
                else:
                    print("Valor inválido, mantendo o valor anterior.")
            else:
                config[key] = new_value

    # --- Escolha da pasta de textos (subpasta dentro de "./copys") ---
    copys_dir = "./copys"
    if os.path.exists(copys_dir) and os.path.isdir(copys_dir):
        subdirs = [d for d in os.listdir(copys_dir) if os.path.isdir(os.path.join(copys_dir, d))]
        if subdirs:
            print("\nPastas disponíveis em './copys':")
            for i, sub in enumerate(subdirs, start=1):
                print(f"{i}: {sub}")
            choice = input("Digite o número da pasta desejada (ou pressione Enter para manter o valor atual): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(subdirs):
                        config["copy_text_folder"] = subdirs[index]
                        print(f"Pasta selecionada: {subdirs[index]}")
                    else:
                        print("Número inválido. Mantendo o valor atual.")
                except:
                    print("Entrada inválida. Mantendo o valor atual.")
            else:
                print("Mantendo o valor atual para a pasta de textos.")
    else:
        print("A pasta './copys' não existe.")

    # --- Escolha da pasta de imagens (subpasta dentro de change-img) ---
    change_img_dir = "change-img"
    if os.path.exists(change_img_dir) and os.path.isdir(change_img_dir):
        subdirs = [d for d in os.listdir(change_img_dir) if os.path.isdir(os.path.join(change_img_dir, d))]
        if subdirs:
            print("\nPastas disponíveis em 'change-img':")
            for i, sub in enumerate(subdirs, start=1):
                print(f"{i}: {sub}")
            choice = input("Digite o número da pasta de imagens desejada (ou pressione Enter para manter o valor atual): ").strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(subdirs):
                        # Atualiza o caminho relativo para a pasta de imagens escolhida
                        config["change_img_folder"] = os.path.join(change_img_dir, subdirs[index])
                        print(f"Pasta de imagens selecionada: {config['change_img_folder']}")
                    else:
                        print("Número inválido. Mantendo o valor atual.")
                except:
                    print("Entrada inválida. Mantendo o valor atual.")
            else:
                print("Mantendo o valor atual para a pasta de imagens.")
        else:
            print("Nenhuma subpasta encontrada em 'change-img'.")
    else:
        print("A pasta 'change-img' não existe.")

    # --- Configuração para o arquivo de chats capturados ---
    new_value = input(f"captured_chats_file [{config.get('captured_chats_file', 'captured_chats.txt')}]: ").strip()
    if new_value:
        config["captured_chats_file"] = new_value

    save_config(config)
    return config

def read_single_key(timeout=10):
    """
    Lê uma única tecla do usuário com timeout.
    Retorna a tecla pressionada ou None se nenhuma tecla for pressionada dentro do timeout.
    """
    import sys
    if os.name == 'nt':
        import msvcrt
        start = time.time()
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                try:
                    return ch.decode('utf-8')
                except:
                    return ch
            if time.time() - start > timeout:
                return None
            time.sleep(0.1)
    else:
        import select, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                ch = sys.stdin.read(1)
                return ch
            else:
                return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_startup_choice(timeout=10):
    """
    Exibe a mensagem inicial e aguarda o input do usuário.
    Retorna 'setup' se o usuário pressionar espaço, ou 'start' caso contrário.
    """
    print("Aperte Enter para iniciar o programa ou espaço para entrar no setup.")
    print(f"Aguardando {timeout} segundos...")
    key = read_single_key(timeout)
    if key is None:
        print("Nenhuma tecla pressionada. Iniciando com configurações padrão...")
        return 'start'
    if key == ' ':
        return 'setup'
    else:
        return 'start'

def calculate_folder_size(folder):
    """
    Calcula o tamanho total de uma pasta (em bytes).
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def monitor_user_data_dir(config):
    """
    Verifica se a pasta referenciada por user_data_dir ultrapassa o tamanho limite configurado.
    Se ultrapassar, pergunta ao usuário se deseja apagar a pasta de sessão.
    """
    if not config.get("monitor_user_data_dir", True):
        return

    user_data_dir = config.get("user_data_dir")
    threshold_gb = config.get("user_data_dir_size_threshold_gb", 2)
    
    if os.path.exists(user_data_dir):
        folder_size_bytes = calculate_folder_size(user_data_dir)
        folder_size_gb = folder_size_bytes / (1024 ** 3)
        if folder_size_gb > threshold_gb:
            print(f"\nA pasta de sessão '{user_data_dir}' tem {folder_size_gb:.2f}GB, ultrapassando o limite de {threshold_gb}GB.")
            resposta = input("Deseja apagar a pasta de sessão? [y/s para sim, Enter para não]: ").strip().lower()
            if resposta in ["y", "s"]:
                try:
                    shutil.rmtree(user_data_dir)
                    os.makedirs(user_data_dir)
                    print("Pasta de sessão apagada e recriada.")
                except Exception as e:
                    print(f"Erro ao apagar a pasta de sessão: {e}")
            else:
                print("Mantendo a pasta de sessão.")
    else:
        print(f"A pasta de sessão '{user_data_dir}' não existe. Será criada automaticamente.")

# ====================================================
# Classe de Automação do WhatsApp
# ====================================================

class WhatsCliker:
    def __init__(self, driver, scroll_increment=300, sleep_time=0.5, copy_text_folder="", config=None):
        """
        Inicializa a classe.
          - driver: instância do Selenium (undetected_chromedriver)
          - scroll_increment: incremento do scroll no painel de chats
          - sleep_time: tempo de espera entre as ações
          - copy_text_folder: nome da subpasta (dentro de "./copys") de onde os arquivos de texto serão lidos.
          - config: dicionário de configurações (para acessar a pasta de imagens, etc.)
        """
        self.driver = driver
        self.scroll_increment = scroll_increment
        self.sleep_time = sleep_time
        self.config = config or {}
        self.captured_chats = set()  # Chats capturados durante o scroll
        # Define a pasta dos textos: se copy_text_folder estiver configurado, usa "./copys/<copy_text_folder>"
        self.folder_path = os.path.join("./copys", copy_text_folder) if copy_text_folder else "./copys"
        self.retrieved_chats_from_file = set()  # Chats carregados de arquivo

    def acessar_whatsapp(self):
        """
        Configura a janela do navegador, acessa o WhatsApp Web e aguarda o carregamento da sessão.
        """
        self.driver.set_window_size(960, 1080)
        self.driver.set_window_position(0, 0)
        self.driver.get("https://web.whatsapp.com")
        print("Aguarde enquanto a sessão é carregada...")

        try:
            WebDriverWait(self.driver, 900).until(
                EC.presence_of_element_located((By.ID, "pane-side"))
            )
            print("Login realizado e sessão carregada com sucesso!")
        except Exception as e:
            print("Erro ao carregar a sessão:", e)
            traceback.print_exc()
            self.driver.quit()

    def scroll_and_capture(self):
        """
        Realiza o scroll no painel lateral para capturar os nomes dos chats.
        O processo continua até que o usuário pressione Enter.
        """
        try:
            pane_side = self.driver.find_element(By.ID, "pane-side")
        except Exception as e:
            print(f"Erro ao localizar o painel de chats: {e}")
            return

        print("Iniciando captura de chats com scroll... (Pressione Enter para parar)")
        try:
            while True:
                # --- SCROLL PARA BAIXO ---
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

                    previous_scroll = self.driver.execute_script("return arguments[0].scrollTop;", pane_side)
                    self.driver.execute_script("arguments[0].scrollTop += arguments[1];", pane_side, self.scroll_increment)
                    time.sleep(self.sleep_time)
                    current_scroll = self.driver.execute_script("return arguments[0].scrollTop;", pane_side)
                    if current_scroll == previous_scroll:
                        break

                # --- SCROLL PARA O TOPO ---
                while True:
                    previous_scroll = self.driver.execute_script("return arguments[0].scrollTop;", pane_side)
                    self.driver.execute_script("arguments[0].scrollTop -= arguments[1];", pane_side, self.scroll_increment)
                    time.sleep(self.sleep_time)
                    if previous_scroll == 0:
                        break

                if self._stop_requested():
                    print("\nCaptura interrompida pelo usuário.")
                    break

        except Exception as e:
            print(f"Erro durante o scroll: {e}")

        print("\nCaptura finalizada. Chats capturados:")
        for idx, chat in enumerate(self.captured_chats, start=1):
            print(f"{idx}. {chat}")

    def _stop_requested(self):
        """
        Verifica se o usuário pressionou Enter para interromper o processo.
        """
        import sys, select
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            return True
        return False

    def save_chats_to_file(self, filename=None):
        """
        Salva os chats capturados em um arquivo de texto.
        """
        if not self.captured_chats:
            print("Nenhum chat capturado para salvar.")
            return

        if not filename:
            # Usa o valor configurado, se existir
            filename = self.config.get("captured_chats_file", "captured_chats.txt")
        try:
            with open(filename, "w", encoding="utf-8") as file:
                for chat in sorted(self.captured_chats):
                    file.write(f"{chat}\n")
            print(f"Chats salvos com sucesso em: {filename}")
        except Exception as e:
            print(f"Erro ao salvar os chats: {e}")

    def load_chats_from_file(self, filename=None):
        """
        Carrega os chats de um arquivo de texto e os retorna como um conjunto.
        Se o parâmetro 'filename' não for informado, utiliza o valor configurado
        em 'captured_chats_file'.
        """
        if filename is None:
            filename = self.config.get("captured_chats_file", "captured_chats.txt")
        if not os.path.exists(filename):
            print(f"Arquivo {filename} não encontrado.")
            return set()

        with open(filename, "r", encoding="utf-8") as file:
            chats = {line.strip() for line in file if line.strip()}
        self.retrieved_chats_from_file = chats

        print("Chats carregados do arquivo:")
        for idx, chat in enumerate(chats, start=1):
            print(f"{idx}. {chat}")

        return chats


    def filter_chats_to_exclusion_file(self, chats, exclusion_file="exclusion_file.txt"):
        """
        Permite que o usuário adicione chats a um arquivo de exclusão.
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
            print(f"Erro ao processar exclusões: {e}")

    def scroll_and_find(self, target_chats, exclusion_zone):
        try:
            pane_side = self.driver.find_element(By.ID, "pane-side")
        except Exception as e:
            print(f"Erro ao localizar o painel de chats: {e}")
            return set()  

        found_chats = set()
        previous_count = 0

        # Loop até que não sejam encontrados novos chats
        while (target_chats - found_chats - exclusion_zone):
            print(f"\nChats restantes para processar: {len(target_chats - found_chats - exclusion_zone)}")
            
            self._process_visible_chats(pane_side, target_chats, found_chats, exclusion_zone)
            
            # Se o número de chats encontrados não aumentar, tenta fazer scroll e verifica novamente
            if len(found_chats) == previous_count:
                if not self._scroll_down(pane_side):
                    print("Não foi possível rolar mais. Encerrando busca.")
                    break
            else:
                previous_count = len(found_chats)
        
        self._scroll_to_top(pane_side)
        
        if target_chats:
            lost_chats = target_chats - found_chats - exclusion_zone
            quantidade = len(lost_chats)
            print(f"Chats não processados: {quantidade}")
            for idx, chat in enumerate(lost_chats, start=1):
                print(f"{idx} - {chat}")
        else:
            print("Todos os chats foram processados!")
            
        print("\nProcesso de disparo finalizado.")
        if found_chats:
            print("Chats processados:")
            for idx, chat in enumerate(found_chats, start=1):
                print(f"{idx} - {chat}")
        else:
            print("Nenhum chat especificado foi encontrado.")

        return found_chats

    def _process_visible_chats(self, pane_side, target_chats, found_chats, exclusion_zone):
        """
        Processa os chats visíveis na tela que fazem parte de target_chats.
        """
        chats = pane_side.find_elements(By.XPATH, './/*[@role="listitem"]')
        for chat in chats:
            try:
                title_element = chat.find_element(By.XPATH, './/span[@title]')
                title = title_element.get_attribute("title")
                if title in target_chats and title not in found_chats and title not in exclusion_zone:
                    self._process_chat(chat, title)
                    found_chats.add(title)
            except Exception:
                continue

    def _process_chat(self, chat, title):
        try:
            print(f"Processando chat: {title}")
            xpath = f'//*[@title="{title}"]'
            # Tenta obter o elemento clicável com retry
            chat_to_click = None
            retries = 3
            for attempt in range(retries):
                try:
                    chat_to_click = WebDriverWait(self.driver, 45).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    break  # Se obtivermos o elemento, saímos do loop
                except StaleElementReferenceException as e:
                    print(f"Tentativa {attempt+1}: Elemento stale. Re-localizando...")
                    time.sleep(1)
            if chat_to_click is None:
                raise Exception("Não foi possível localizar o elemento clicável.")
            
            # Garante que o elemento esteja visível
            self.driver.execute_script("arguments[0].scrollIntoView(true);", chat_to_click)
            time.sleep(2)  # Pequeno delay para estabilidade

            try:
                chat_to_click.click()
            except Exception as click_error:
                print(f"Click interceptado, tentando via JavaScript: {click_error}")
                self.driver.execute_script("arguments[0].click();", chat_to_click)
            
            time.sleep(1)
            self._clear_chat()
            self._send_random_message()
            self.click_attach_button()
            self.click_photo_attach_button()

            delay = random.uniform(9, 35)
            print(f"Aguardando {delay:.2f} segundos antes do próximo chat.")
            time.sleep(delay)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", chat)
        except Exception as e:
            print(f"Erro ao processar o chat '{title}': {e}")

    def _scroll_down(self, pane_side):
        previous_scroll = self.driver.execute_script("return arguments[0].scrollTop;", pane_side)
        self.driver.execute_script("arguments[0].scrollTop += arguments[1];", pane_side, self.scroll_increment)
        time.sleep(self.sleep_time)
        current_scroll = self.driver.execute_script("return arguments[0].scrollTop;", pane_side)
        return current_scroll != previous_scroll

    def _scroll_to_top(self, pane_side):
        while self.driver.execute_script("return arguments[0].scrollTop;", pane_side) > 0:
            self.driver.execute_script("arguments[0].scrollTop -= arguments[1];", pane_side, self.scroll_increment)
            time.sleep(self.sleep_time)

    def _clear_chat(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@id="main"]//button[@aria-label="Mais opções" and @title="Mais opções"]')
                )
            ).click()
            print("Clicou em 'Mais opções'.")
        except Exception as e:
            print(f"Erro ao clicar em 'Mais opções': {e}")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@aria-label="Limpar conversa" and text()="Limpar conversa"]')
                )
            ).click()
            print("Clicou em 'Limpar conversa'.")
        except Exception as e:
            print(f"Erro ao clicar em 'Limpar conversa': {e}")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[.//div[contains(text(), "Limpar conversa")]]')
                )
            ).click()
            print("Confirmação de limpeza efetuada.")
        except Exception as e:
            print(f"Erro ao confirmar a limpeza: {e}")

        time.sleep(3)

    def _send_random_message(self):
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
                print("Mensagem enviada na caixa de texto.")
            else:
                print(f"O arquivo selecionado ({random_file}) está vazio.")
        except FileNotFoundError as e:
            print(f"Arquivo não encontrado: {e}")
        except Exception as e:
            print(f"Erro ao enviar a mensagem: {e}")

    def _get_random_txt_file(self):
        if not os.path.exists(self.folder_path):
            raise FileNotFoundError(f"Pasta '{self.folder_path}' não encontrada.")
        txt_files = [f for f in os.listdir(self.folder_path) if f.endswith(".txt")]
        if not txt_files:
            raise FileNotFoundError("Nenhum arquivo .txt encontrado na pasta.")
        return random.choice(txt_files)

    def click_attach_button(self):
        try:
            WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div/div/div[3]/div/div[4]/div/footer/div[1]/div/span/div/div[1]/div/button/span")
                )
            ).click()
            print("Botão de anexar clicado.")
        except Exception as e:
            print(f"Erro ao clicar no botão de anexar: {e}")

    def click_photo_attach_button(self):
        try:
            image_path = self.handle_file_dialog()
            if image_path is None:
                print("Nenhuma imagem selecionada.")
                return
            input_file = self.driver.find_element(
                By.XPATH, 
                '//input[@type="file" and @accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
            )
            input_file.send_keys(image_path)
            WebDriverWait(self.driver, 45).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@role="button" and @aria-label="Enviar"]')
                )
            ).click()
            print("Imagem enviada com sucesso.")
        except Exception as e:
            print(f"Erro no upload da imagem: {e}")
            traceback.print_exc()

    def handle_file_dialog(self):
        try:
            image_path = self.get_random_image_path()
            print(f"Imagem selecionada: {image_path}")
            return image_path
        except Exception as e:
            print(f"Erro ao selecionar imagem: {e}")
            return None

    def get_random_image_path(self):
        change_img_folder = self.config.get("change_img_folder", "change-img")
        if not os.path.exists(change_img_folder):
            raise FileNotFoundError(f"Pasta de imagens '{change_img_folder}' não encontrada.")
        subdirs = [d for d in os.listdir(change_img_folder) if os.path.isdir(os.path.join(change_img_folder, d))]
        chosen_folder = os.path.join(change_img_folder, random.choice(subdirs)) if subdirs else change_img_folder
        allowed_exts = [".jpg", ".jpeg", ".png", ".gif"]
        images = [f for f in os.listdir(chosen_folder) if os.path.splitext(f)[1].lower() in allowed_exts]
        if not images:
            raise FileNotFoundError(f"Nenhuma imagem encontrada na pasta '{chosen_folder}'.")
        chosen_image = os.path.join(chosen_folder, random.choice(images))
        return os.path.abspath(chosen_image)

    def execute_function_prompt(self, function):
        func_name = function.__name__ if hasattr(function, '__name__') else str(function)
        resposta = input(f"Deseja executar {func_name}? [y/s para sim, Enter para não]: ").strip().lower()
        if resposta in ["y", "s"]:
            print(f"Executando {func_name}...")
            function()
        else:
            print(f"{func_name} não será executada.")

# ====================================================
# Função Principal
# ====================================================

def main():
    choice = get_startup_choice(timeout=10)
    if choice == 'setup':
        config = setup_config()
    else:
        config = load_config()

    monitor_user_data_dir(config)
    start_time = time.time()
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={config['user_data_dir']}")
    options.add_argument(f"--user-agent={config['user_agent']}")
    driver = uc.Chrome(options=options)
    wc = WhatsCliker(
        driver,
        scroll_increment=config["scroll_increment"],
        sleep_time=config["sleep_time"],
        copy_text_folder=config.get("copy_text_folder", ""),
        config=config
    )
    wc.acessar_whatsapp()
    if config.get("execute_scroll_and_capture", True):
        wc.scroll_and_capture()
    else:
        print("scroll_and_capture não será executado conforme a configuração.")
    if config.get("execute_save_chats_to_file", True):
        wc.save_chats_to_file()
    else:
        print("save_chats_to_file não será executado conforme a configuração.")
    chats = wc.load_chats_from_file()
    if config.get("execute_filter_chats", True):
        wc.filter_chats_to_exclusion_file(chats)
    else:
        print("filter_chats (exclusão) não será executado conforme a configuração.")
    exclusion_chats = wc.load_chats_from_file("exclusion_file.txt")
    wc.scroll_and_find(chats, exclusion_chats)
    elapsed_time = (time.time() - start_time) / 60
    print(f"Tempo total de execução: {elapsed_time:.2f} minutos")
    exit_delay = config.get("exit_delay", 15)
    time_to_sleep = input(f"Insira o tempo de espera (em segundos) antes de encerrar (padrão {exit_delay}): ") or exit_delay
    print(f"Aguardando {time_to_sleep} segundos antes de encerrar...")
    time.sleep(int(time_to_sleep))
    driver.quit()

if __name__ == "__main__":
    main()
