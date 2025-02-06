#!/bin/bash

WETH_USER="weth"
WETH_HOME="/opt/$WETH_USER"
WETH_HOME_EXT="/opt/$WETH_USER/${WETH_USER}-server"

# O padrão de porta para a instância WETH (se você usar o comando -c no terminal)
INSTALL_WKHTMLTOPDF="True"

# Defina a porta padrão do WETH (você ainda precisará usar -c /opt/weth-server.conf, por exemplo, para usá-la)
WETH_PORT="8069"

# Escolha a versão do WETH que você deseja instalar, como 13.0, 12.0, 11.0 ou saas-18. Ao usar 'master', a versão master será instalada.
WETH_VERSION="master"

# Defina isso como True se você quiser instalar o Nginx!
INSTALL_NGINX="False"

# Defina a senha do superadmin. Se GENERATE_RANDOM_PASSWORD estiver definido como "True", geraremos uma senha aleatória, caso contrário, usaremos a definida aqui.
WETH_SUPERADMIN="weth"

# Defina como "True" para gerar uma senha aleatória ou "False" para usar a variável WETH_SUPERADMIN
GENERATE_RANDOM_PASSWORD="True"

WETH_CONFIG="${WETH_USER}-server"

# Defina o nome do site
WEBSITE_NAME="_"

# Defina a porta padrão do longpolling do WETH (você ainda precisará usar -c /opt/weth-server.conf, por exemplo, para usá-la)
LONGPOLLING_PORT="8072"

# Defina como "True" para instalar o Certbot e habilitar SSL, ou "False" para usar HTTP
ENABLE_SSL="True"

# Forneça o e-mail para registrar o certificado SSL
ADMIN_EMAIL="weth@weth.com.br"

## 
### Links para download do WKHTMLTOPDF

WKHTMLTOX_X64=https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.trusty_amd64.deb
WKHTMLTOX_X32=https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.trusty_i386.deb

#--------------------------------------------------
# Atualizar o servidor
#--------------------------------------------------
echo -e "\n---- Atualizando o servidor ----"
# O pacote universe é necessário para o Ubuntu 18.x
sudo add-apt-repository universe
# Dependência libpng12-0 para wkhtmltopdf
sudo add-apt-repository "deb http://mirrors.kernel.org/ubuntu/ xenial main"
sudo apt-get update
sudo apt-get upgrade -y

#--------------------------------------------------
# Instalar o PostgreSQL
#--------------------------------------------------
echo -e "\n---- Instalando o servidor PostgreSQL ----"
sudo apt-get install postgresql postgresql-server-dev-all -y

echo -e "\n---- Criando o usuário do PostgreSQL para o WETH ----"
sudo su - postgres -c "createuser -s $WETH_USER" 2> /dev/null || true

#--------------------------------------------------
# Instalar dependências
#--------------------------------------------------
echo -e "\n--- Instalando Python 3 + pip3 --"
sudo apt-get install git python3 python3-pip build-essential wget python3-dev python3-venv python3-wheel libxslt-dev libzip-dev libldap2-dev libsasl2-dev python3-setuptools node-less libpng12-0 libjpeg-dev gdebi -y

echo -e "\n---- Instalando pacotes/python requisitados ----"
sudo -H pip3 install -r https://github.com/thiago95macedo/weth/raw/${WETH_VERSION}/requirements.txt

echo -e "\n---- Instalando NodeJS NPM e rtlcss para suporte LTR ----"
sudo apt-get install nodejs npm -y
sudo npm install -g rtlcss

#--------------------------------------------------
# Instalar WKHTMLTOPDF se necessário
#--------------------------------------------------
if [ $INSTALL_WKHTMLTOPDF = "True" ]; then
  echo -e "\n---- Instalando wkhtmltopdf e criando atalhos para o WETH ----"
  if [ "`getconf LONG_BIT`" == "64" ]; then
      _url=$WKHTMLTOX_X64
  else
      _url=$WKHTMLTOX_X32
  fi
  sudo wget $_url
  sudo gdebi --n `basename $_url`
  sudo ln -s /usr/local/bin/wkhtmltopdf /usr/bin
  sudo ln -s /usr/local/bin/wkhtmltoimage /usr/bin
else
  echo "Wkhtmltopdf não será instalado conforme escolha do usuário!"
fi

echo -e "\n---- Criando o usuário do sistema para o WETH ----"
sudo adduser --system --quiet --shell=/bin/bash --home=$WETH_HOME --gecos 'WETH' --group $WETH_USER
# O usuário também será adicionado ao grupo 'sudo'.
sudo adduser $WETH_USER sudo

echo -e "\n---- Criando o diretório de logs ----"
sudo mkdir /var/log/$WETH_USER
sudo chown $WETH_USER:$WETH_USER /var/log/$WETH_USER

#--------------------------------------------------
# Instalar o WETH
#--------------------------------------------------
echo -e "\n==== Instalando o servidor WETH ===="
sudo git clone --depth 1 --branch $WETH_VERSION https://www.github.com/thiago95macedo/weth $WETH_HOME_EXT/

echo -e "\n---- Criando o diretório customizado do WETH ----"
sudo su $WETH_USER -c "mkdir $WETH_HOME/custom"
sudo su $WETH_USER -c "mkdir $WETH_HOME/custom/addons"

#--------------------------------------------------
# Alteração para garantir permissões no diretório de instalação
#--------------------------------------------------
echo -e "\n---- Definindo permissões no diretório home e no diretório de instalação ----"
sudo chown -R $WETH_USER:$WETH_USER $WETH_HOME
sudo chmod -R 775 $WETH_HOME
sudo chmod -R 775 $WETH_HOME_EXT

#--------------------------------------------------
# Criando o arquivo de configuração do servidor
#--------------------------------------------------
echo -e "* Criando o arquivo de configuração do servidor"
sudo touch /opt/${WETH_CONFIG}.conf
echo -e "* Criando arquivo de configuração do servidor"
sudo su root -c "printf '[options] \n; Esta é a senha que permite operações no banco de dados:\n' >> /opt/${WETH_CONFIG}.conf"
if [ $GENERATE_RANDOM_PASSWORD = "True" ]; then
    echo -e "* Gerando senha aleatória para o admin"
    WETH_SUPERADMIN=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
fi
sudo su root -c "printf 'admin_passwd = ${WETH_SUPERADMIN}\n' >> /opt/${WETH_CONFIG}.conf"
if [ $WETH_VERSION > "11.0" ]; then
    sudo su root -c "printf 'http_port = ${WETH_PORT}\n' >> /opt/${WETH_CONFIG}.conf"
else
    sudo su root -c "printf 'xmlrpc_port = ${WETH_PORT}\n' >> /opt/${WETH_CONFIG}.conf"
fi
sudo su root -c "printf 'logfile = /var/log/${WETH_USER}/${WETH_CONFIG}.log\n' >> /opt/${WETH_CONFIG}.conf"

echo -e "* Criando o arquivo de inicialização"
sudo su root -c "echo '#!/bin/sh' >> $WETH_HOME_EXT/start.sh"
sudo su root -c "echo 'sudo -u $WETH_USER $WETH_HOME_EXT/weth-bin --config=/opt/${WETH_CONFIG}.conf' >> $WETH_HOME_EXT/start.sh"
sudo chmod 755 $WETH_HOME_EXT/start.sh

#--------------------------------------------------
# Adicionando o WETH como um daemon (initscript)
#--------------------------------------------------
echo -e "* Criando arquivo init"
cat <<EOF > ~/$WETH_CONFIG
#!/bin/sh
### BEGIN INIT INFO
# Provides: $WETH_CONFIG
# Required-Start: \$remote_fs \$syslog
# Required-Stop: \$remote_fs \$syslog
# Should-Start: \$network
# Should-Stop: \$network
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Aplicações Empresariais WETH
# Description: Aplicações de Negócios WETH
### END INIT INFO
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin
DAEMON=$WETH_HOME_EXT/weth-bin
NAME=$WETH_CONFIG
DESC=$WETH_CONFIG
USER=$WETH_USER
CONFIGFILE="/opt/${WETH_CONFIG}.conf"
PIDFILE=/var/run/\${NAME}.pid
DAEMON_OPTS="-c \$CONFIGFILE"
[ -x \$DAEMON ] || exit 0
[ -f \$CONFIGFILE ] || exit 0
checkpid() {
[ -f \$PIDFILE ] || return 1
pid=\`cat \$PIDFILE\`
[ -d /proc/\$pid ] && return 0
return 1
}
case "\${1}" in
start)
echo -n "Starting \$NAME: "
start-stop-daemon --start --quiet --pidfile \$PIDFILE --exec \$DAEMON -- \$DAEMON_OPTS
echo "\$NAME started"
;...
EOF

# Ajuste de permissões no arquivo init
sudo mv ~/$WETH_CONFIG /etc/init.d/
sudo chmod 755 /etc/init.d/$WETH_CONFIG
sudo update-rc.d $WETH_CONFIG defaults

# Finalizando e executando o WETH
echo -e "\n---- Iniciando o servidor WETH ----"
sudo /etc/init.d/$WETH_CONFIG start
