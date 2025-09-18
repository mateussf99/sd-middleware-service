import subprocess
import sys
import shutil
import os

def run_migration_commands():
    """
    Executa os comandos de limpeza, inicialização, migração, atualização
    e semeadura (seeding) do banco de dados para um projeto Flask.
    """
    print("Iniciando o processo de migração e semeadura do banco de dados...")

    try:
        # 1. Limpa as pastas de 'instance' e 'migrations'
        print("Executando a limpeza das pastas...")
        folders_to_clean = ['instance', 'migrations']
        for folder in folders_to_clean:
            if os.path.exists(folder) and os.path.isdir(folder):
                print(f"Excluindo a pasta: {folder}")
                shutil.rmtree(folder)
            else:
                print(f"Pasta '{folder}' não encontrada, pulando a exclusão.")
        print("Limpeza concluída.")
        print("---")

        # 2. Executa a inicialização do banco de dados
        print("Executando: flask --app app db init")
        result = subprocess.run(
            ['flask', '--app', 'app', 'db', 'init'],
            check=True,
            text=True,
            capture_output=True
        )
        print("Saída do comando 'db init':")
        print(result.stdout)
        print("---")

        # 3. Cria uma nova migração. O nome da mensagem pode ser personalizado aqui.
        migration_message = "Initial migration"
        print(f"Executando: flask --app app db migrate -m \"{migration_message}\"")
        result = subprocess.run(
            ['flask', '--app', 'app', 'db', 'migrate', '-m', migration_message],
            check=True,
            text=True,
            capture_output=True
        )
        print("Saída do comando 'db migrate':")
        print(result.stdout)
        print("---")

        # 4. Atualiza o banco de dados com a migração
        print("Executando: flask --app app db upgrade")
        result = subprocess.run(
            ['flask', '--app', 'app', 'db', 'upgrade'],
            check=True,
            text=True,
            capture_output=True
        )
        print("Saída do comando 'db upgrade':")
        print(result.stdout)
        print("---")

        # 5. Executa o script de semeadura (seeding)
        print("Executando: python3 seed.py")

        if os.name == 'nt':  # Se o sistema operacional for Windows
            seedCommand = ['py', 'seed.py']
        else:  # Se for 'posix' (Linux, macOS, etc.)
            seedCommand = ['python3', 'seed.py']

        result = subprocess.run(
            seedCommand,
            check=True,
            text=True,
            capture_output=True
        )
        print("Saída do comando 'seed.py':")
        print(result.stdout)
        print("---")

        print("Processo de migração e semeadura concluído com sucesso!")

    except subprocess.CalledProcessError as e:
        print(f"Erro durante a execução do comando: {e.cmd}")
        print(f"Código de retorno: {e.returncode}")
        print(f"Saída de erro:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Erro: O comando 'flask' ou 'python3' não foi encontrado. Certifique-se de que estão instalados e configurados corretamente no seu ambiente virtual.")
        sys.exit(1)

if __name__ == "__main__":
    run_migration_commands()