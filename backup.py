import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

from discord_webhook import DiscordEmbed, DiscordWebhook
from dotenv import load_dotenv



# Carregando informações do ambiente
try:
    load_dotenv()
    RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
    DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
    DISCORD_USER = os.getenv("DISCORD_USER")

    BACKUP_REPO = os.getenv("BACKUP_REPO")
    INCLUDE_LIST = os.getenv("INCLUDE_LIST")
    EXCLUDE_LIST = os.getenv("EXCLUDE_LIST")

    # Não é uma solução perfeita, mas funciona na maior parte
    BACKUP_EXTRA_ARGS = os.getenv("BACKUP_EXTRA_ARGS").split(" ")
    FORGET_EXTRA_ARGS = os.getenv("FORGET_EXTRA_ARGS").split(" ")
    CHECK_EXTRA_ARGS = os.getenv("CHECK_EXTRA_ARGS").split(" ")
    STATS_EXTRA_ARGS = os.getenv("STATS_EXTRA_ARGS").split(" ")

    KEEP_LAST = os.getenv("KEEP_LAST")
    KEEP_DAILY = os.getenv("KEEP_DAILY")
    KEEP_WEEKLY = os.getenv("KEEP_WEEKLY")
    KEEP_MONTHLY = os.getenv("KEEP_MONTHLY")
    KEEP_YEARLY = os.getenv("KEEP_YEARLY")
    KEEP_TAG = os.getenv("KEEP_TAG")
except Exception:
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Algo deu errado com as variáveis de ambiente", file=sys.stderr)
    exit(1)



WEBHOOK_NAME = "Restic Backup"
COLORS = {
    "SUCESSO": "00ff00",
    "AVISO": "ffff00",
    "ERRO": "ff0000",
    "IGNORADO": "0000ff",
}



# Envia uma mensagem de aviso sobre backup para um webhook do Discord,
# contendo informações de erros e avisos se necessário
def send_to_discord(timings, output, stats_output):
    duration = str(timedelta(seconds=timings["end"] - timings["start"]))

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK, title=WEBHOOK_NAME)



    embed_info = DiscordEmbed(title="Informações", color="a0a0a0")
    embed_info.set_author(name=WEBHOOK_NAME, url="https://restic.net/", icon_url="https://restic.readthedocs.io/en/latest/_static/logo.png")
    embed_info.add_embed_field(name="Início", value=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timings['start'])))
    embed_info.add_embed_field(name="Fim", value=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timings['end'])))
    embed_info.add_embed_field(name="Duração", value=f"{duration}")

    embed_info.set_description("```\n" + stats_output["stdout"].replace("\n\n", "\n")[:1024] + "\n" + stats_output["stderr"].replace("\n\n", "\n")[:1024] + "```")



    # Algo deu errado e portanto dê um ping para chamar a atenção do usuário
    if DISCORD_USER and (stats_output["stderr"] or not (output["backup"]["status"] == "SUCESSO" and output["forget"]["status"] == "SUCESSO" and output["check"]["status"] == "SUCESSO")):
        webhook.set_content(f"Chamando {DISCORD_USER} para investigar!!!")



    if timings["stats"]:
        embed_info.set_timestamp(timings["stats"])



    webhook.add_embed(embed_info)



    for key, value in output.items():
        if output[key]["status"] != "SUCESSO":
            embed = DiscordEmbed(title=f"Comando 'restic {key}' finalizado como {output[key]['status']}", color=COLORS[output[key]['status']])
            embed.set_author(name=WEBHOOK_NAME, url="https://restic.net/", icon_url="https://restic.readthedocs.io/en/latest/_static/logo.png")

            embed.set_description("```" + "\n" + " ".join(output[key]["command"]) + "\n" + output[key]["text"]["stdout"][:1024] + "\n" + output[key]["text"]["stderr"][:1024] + "```")

            if timings[key]:
                embed.set_timestamp(timings[key])

            webhook.add_embed(embed)

    webhook.execute()



# Roda um comando especificado e retorna a saída de stdout e stderr
def run_command(command, env=None):
    stdout_lines = []
    stderr_lines = []

    process = subprocess.Popen(" ".join(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, env=env)

    for stdout_line in iter(process.stdout.readline, ""):
        print(stdout_line, end="")
        stdout_lines.append(stdout_line)

    for stderr_line in iter(process.stderr.readline, ""):
        print(stderr_line, end="")
        stderr_lines.append(stderr_line)

    process.stdout.close()
    process.stderr.close()
    return_code = process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command, output="".join(stdout_lines), stderr="".join(stderr_lines))

    return {"stdout": "\n".join(stdout_lines), "stderr": "\n".join(stderr_lines)}



def main():
    # Comandos a serem utilizados
    backup_command = [
        "restic", "backup", "--repo", BACKUP_REPO,
        "--files-from", INCLUDE_LIST,
        "--exclude-file", EXCLUDE_LIST,
    ] + BACKUP_EXTRA_ARGS

    forget_command = [
        "restic", "forget", "--repo", BACKUP_REPO,
        "--keep-last", str(KEEP_LAST),
        "--keep-daily", str(KEEP_DAILY),
        "--keep-weekly", str(KEEP_WEEKLY),
        "--keep-monthly", str(KEEP_MONTHLY),
        "--keep-yearly", str(KEEP_YEARLY),
        "--keep-tag", KEEP_TAG,
        "--prune"
    ] + FORGET_EXTRA_ARGS

    check_command = ["restic", "check", "--repo", BACKUP_REPO] + CHECK_EXTRA_ARGS

    stats_command = ["restic", "stats", "--repo", BACKUP_REPO] + STATS_EXTRA_ARGS



    output = {
        "backup": {"status": "IGNORADO", "command": backup_command, "text": { "stdout": "", "stderr": ""}},
        "forget": {"status": "IGNORADO", "command": forget_command, "text": { "stdout": "", "stderr": ""}},
        "check": {"status": "IGNORADO", "command": check_command, "text": { "stdout": "", "stderr": ""}}
    }

    timings = {
        "start": None,
        "backup": None,
        "forget": None,
        "check": None,
        "stats": None,
        "end": None,
    }



    # Carregando a senha
    env = os.environ.copy()
    env["RESTIC_PASSWORD"] = RESTIC_PASSWORD



    timings["start"] = time.time()



    # Executando todos os comandos
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Começando backup...")

        # Boa prática de desbloquear o repositório no início de uma operação
        print(f"restic unlock --repo {BACKUP_REPO}")
        subprocess.run(["restic", "unlock", "--repo", BACKUP_REPO])

        print(" ".join(backup_command))
        timings["backup"] = time.time()
        output["backup"]["text"] = run_command(backup_command, env=env)
        output["backup"]["status"] = "SUCESSO"

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Limpando snapshots antigas...")
        print(" ".join(forget_command))
        timings["forget"] = time.time()
        output["forget"]["text"] = run_command(forget_command, env=env)
        output["forget"]["status"] = "SUCESSO"

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Verificando integridade do repositório...")
        print(" ".join(check_command))
        timings["check"] = time.time()
        output["check"]["text"] = run_command(check_command, env=env)
        output["check"]["status"] = "SUCESSO"
    except subprocess.CalledProcessError as e:
        e_output = {"stdout": e.stdout, "stderr": e.stderr}
        e_type = e.cmd[1]

        # Se houver um erro, mas for no comando 'check' ou o código de retorno é 3 marcar como apenas um aviso
        # https://restic.readthedocs.io/en/stable/075_scripting.html#exit-codes
        output[e_type]["text"] = e_output
        output[e_type]["status"] = "AVISO" if (e.cmd == "check" or e.returncode == 3) else "ERRO"

    timings["end"] = time.time()



    # Consegue estatísticas do repositório para serem exibidas na mensagem
    try:
        timings["stats"] = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Conseguindo estatísticas")
        print(" ".join(stats_command))
        stats_output = run_command(stats_command, env=env)
    except subprocess.CalledProcessError as e:
        stats_output = {"stdout": e.stdout, "stderr": e.stderr}



    send_to_discord(timings, output, stats_output)



    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Backup concluído")



if __name__ == "__main__":
    main()
