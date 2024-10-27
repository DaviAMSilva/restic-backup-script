# Restic Backup Script

Esse é um script escrito em Python que eu uso para realizar o backup de meu sistema e de meus arquivos usando a ferramenta [restic](https://restic.net).

A vantagem desse script comparado com utilizar restic diretamente é a integração com um Discord webhook para enviar mensagens de estatísticas de backup e notificações de avisos ou erros durante o processo de backup.

> [!NOTE]
> Assume-se nesses exemplos que o local em que o script está armazenado é `/home/USER/restic` (aonde USER é o nome do usuário realizando o backup) e que o repositório de backup se encontra em `/mnt/HDD/restic`.

> [!WARNING]
> Esse script foi testado apenas em um sistema Linux, mas provavelmente também funcionaria em um sistema Windows.

## Configurando

Baixe o script:

```bash
git clone "https://github.com/DaviAMSilva/restic-backup-script" "~/restic"
```

Instale as dependências diretamente ou usando um ambiente virtual:

```bash
cd ~/restic

# Diretamente
pip3 install -r requirements.txt

# Ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

Renomeie os arquivos de exemplo:

```bash
cd ~/restic

mv include_list.example.txt include_list.txt
mv exclude_list.example.txt exclude_list.txt
mv .env.example .env

# Serve para garantir que apenas um usuário com acesso root tenha acesso ao conteúdo do arquivo
# Isso é opcional e serve para proteger a senha do repositório
# Nesse caso será necessário executar o cron job como root
sudo chown root:root .env
sudo chmod 700 .env
```

Edite os arquivos de inclusão e exclusão de acordo com a documentação do [restic](https://restic.readthedocs.io/en/stable/040_backup.html#excluding-files) e o arquivo de variáveis de ambiente de acordo com o exemplo abaixo:

```dotenv
RESTIC_PASSWORD="senha123"
DISCORD_WEBHOOK="https://discord.com/api/webhooks/██████████/██████████"
DISCORD_USER="<@██████████████████>"

BACKUP_REPO="/mnt/HDD/restic"
INCLUDE_LIST="/home/USER/restic/include_list.txt"
EXCLUDE_LIST="/home/USER/restic/exclude_list.txt"

BACKUP_EXTRA_ARGS="--tag python"
FORGET_EXTRA_ARGS=""
CHECK_EXTRA_ARGS=""

RETENTION_LAST="10"
RETENTION_DAILY="7"
RETENTION_WEEKLY="4"
RETENTION_MONTHLY="12"
RETENTION_YEARLY="1"
KEEP_TAG="keep"
```

[<small>Como criar um webhook no Discord</small>](https://support.discord.com/hc/pt-br/articles/228383668-Usando-Webhooks) — [<small>Onde encontrar o seu ID de usuário do Discord</small>](https://support.discord.com/hc/pt-br/articles/206346498-Onde-posso-encontrar-minhas-IDs-de-usu%C3%A1rio-servidore-mensagem)

## Realizando o backup

### Manualmente

```bash
cd ~/restic

# Diretamente:
python3 backup.py

# Utilizando o ambiente virtual
source venv/bin/activate
python3 backup.py

# Ou, alternativamente:
~/restic/venv/bin/python3
```

### Automaticamente, usando [cron](https://en.wikipedia.org/wiki/Cron)

A seguinte configuração cron realizará o backup todo dia meia-noite, salvando os resultados do comando em arquivos de log:

```crontab
0 0 * * * /home/USER/restic/venv/bin/python3 /home/USER/restic/backup.py >> /home/USER/restic/restic.log 2>&1
```

Use o comando `crontab -e` para editar a sua configuração cron e inserir a configuração acima. Ou, se precisar realizar o backup como root, faça a mesma edição, mas utilizando-se da função sudo: `sudo crontab -e`.

> [!NOTE]
> No sistema Windows a ferramenta equivalente para automatização desse tipo é o Agendador de Tarefas.
