import os
import sys
import time
import signal

from undetected_chromedriver import Chrome, ChromeOptions

# Função para capturar uma tecla (cross-platform)
def get_key():
    """
    Captura uma tecla do usuário.
    Retorna:
      - 'enter' se o usuário pressionar ENTER;
      - 'space' se pressionar a barra de espaço;
      - 'up', 'down', 'left' ou 'right' se pressionar uma seta;
      - ou a própria tecla (string) para outros caracteres.
    """
    try:
        # Para sistemas Unix-like
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            # Se for a tecla de escape, pode ser uma seta (sequência começa com \x1b)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    mapping = {"A": "up", "B": "down", "C": "right", "D": "left"}
                    return mapping.get(ch3, None)
            elif ch in ("\r", "\n"):
                return "enter"
            elif ch == " ":
                return "space"
            else:
                return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except ImportError:
        # Para Windows
        import msvcrt
        ch = msvcrt.getch()
        if ch == b'\xe0':  # tecla especial (setas)
            ch = msvcrt.getch()
            mapping = {b'H': "up", b'P': "down", b'K': "left", b'M': "right"}
            return mapping.get(ch, None)
        elif ch in (b'\r', b'\n'):
            return "enter"
        elif ch == b' ':
            return "space"
        else:
            return ch.decode('utf-8')

class GroupAssessor:
    def __init__(self,
                 filtered_file="grupos_ativos.txt",
                 promising_file="promissores.txt",
                 evaluate_file="avaliar_depois.txt",
                 blacklist_file="blacklist.txt"):
        self.filtered_file = filtered_file
        self.promising_file = promising_file
        self.evaluate_file = evaluate_file
        self.blacklist_file = blacklist_file

        self.urls = []           # URLs dos grupos filtrados
        self.processed_urls = set()  # URLs já classificadas
        self.current_index = 0   # Para salvar o progresso (caso seja necessário)
        self.driver = None
        self.state_file = "state_assessment.txt"

        # Configurar o tratamento de CTRL+C para salvar o progresso
        signal.signal(signal.SIGINT, self.handle_interrupt)

        self.load_urls()
        self.load_processed()
        self.load_state()

    def load_urls(self):
        if not os.path.exists(self.filtered_file):
            print(f"Arquivo {self.filtered_file} não encontrado!")
            sys.exit(1)
        with open(self.filtered_file, 'r', encoding='utf-8') as f:
            self.urls = [line.strip() for line in f if line.strip()]

    def load_processed(self):
        """Carrega URLs que já foram classificadas para não processá-las novamente."""
        for filename in [self.promising_file, self.evaluate_file, self.blacklist_file]:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            self.processed_urls.add(url)

    def load_state(self):
        """Carrega o índice salvo (se existir) para retomar o processamento."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.current_index = int(f.read().strip())
                print(f"Retomando a partir do índice {self.current_index}...")
            except Exception:
                self.current_index = 0

    def save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            f.write(str(self.current_index))

    def handle_interrupt(self, signum, frame):
        print("\nInterrupção detectada. Salvando progresso...")
        self.save_state()
        if self.driver:
            self.driver.quit()
        sys.exit(0)

    def setup_driver(self):
        options = ChromeOptions()
        # Comente a linha abaixo se quiser ver o navegador
        # options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = Chrome(options=options)

    def write_url(self, filename, url):
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(url + "\n")

    def process_urls(self):
        self.setup_driver()
        total = len(self.urls)
        print(f"\nForam encontrados {total} grupos na lista filtrada.")
        print("Para cada grupo, visualize-o no navegador e, no terminal, pressione:")
        print("  • [ENTER] para classificar como 'avaliar depois'")
        print("  • [ESPAÇO] para classificar como 'promissor'")
        print("  • [UMA DAS SETAS] para classificar como 'blacklist'\n")

        try:
            for i in range(self.current_index, total):
                url = self.urls[i]
                self.current_index = i  # atualizar o índice atual

                # Se o URL já foi classificado, pula
                if url in self.processed_urls:
                    continue

                print(f"\n[{i+1}/{total}] Acessando: {url}")
                try:
                    self.driver.get(url)
                except Exception as e:
                    print(f"Erro ao acessar {url}: {e}")
                    # Se der erro no acesso, podemos, por exemplo, tratar como 'avaliar depois'
                    self.write_url(self.evaluate_file, url)
                    self.processed_urls.add(url)
                    continue

                print("Observe o grupo no navegador.")
                print("Pressione a tecla correspondente à classificação:")
                print("  [ENTER] -> avaliar depois")
                print("  [ESPAÇO] -> promissor")
                print("  [SETAS]  -> blacklist")

                key = None
                # Loop até pressionar uma tecla válida
                while key not in ("enter", "space", "up", "down", "left", "right"):
                    key = get_key()

                if key == "enter":
                    self.write_url(self.evaluate_file, url)
                    print("Classificado como: AVALIAR DEPOIS")
                elif key == "space":
                    self.write_url(self.promising_file, url)
                    print("Classificado como: PROMISSOR")
                elif key in ("up", "down", "left", "right"):
                    self.write_url(self.blacklist_file, url)
                    print("Classificado como: BLACKLIST")
                else:
                    # Este ramo não deve ocorrer, mas por segurança:
                    self.write_url(self.evaluate_file, url)
                    print("Classificado (default) como: AVALIAR DEPOIS")

                self.processed_urls.add(url)
                # Salva o estado a cada iteração (para evitar perda de progresso)
                self.save_state()

                # Pequena pausa para não sobrecarregar o navegador
                time.sleep(1)

            print("\nProcessamento concluído!")
        finally:
            self.save_state()
            if self.driver:
                self.driver.quit()
            # Se tudo estiver processado, podemos remover o arquivo de estado
            if os.path.exists(self.state_file):
                os.remove(self.state_file)

if __name__ == "__main__":
    assessor = GroupAssessor(
        filtered_file="grupos_ativos.txt",
        promising_file="promissores.txt",
        evaluate_file="avaliar_depois.txt",
        blacklist_file="blacklist.txt"
    )
    assessor.process_urls()

