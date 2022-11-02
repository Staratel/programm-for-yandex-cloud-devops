import time

import re
import subprocess
import sys
import zipfile
from colorama import init, Fore
from colorama import Back
from colorama import Style
connectIdAndDbHostId = ""
nameAccount = ''
token = ''

def ExCommands(textComands, communic):
    return str(subprocess.Popen(textComands, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate(communic))


def GettingIDServiceAccount(nameAccount):
    prog_config = ['powershell', f'yc iam service-account get --name {nameAccount}']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idAccount = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Идентификатор сервисного аккаунта:', idAccount)
    return idAccount


def AddRoleAccount(folderId, serviceId, roles):
    for role in roles.split(" "):
        prog_config = ['powershell', f'yc resource-manager folder add-access-binding {folderId} '
                                     f'--subject serviceAccount:{serviceId} '
                                     f'--role {role}']
        subprocess.Popen(prog_config, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)


def YcInitAccount():
    global nameAccount
    global token
    nameAccount, token = input("Введите имя, токен через пробел: ").split(" ")
    comm = b"2\n%b\n%b\n1\n\n2\n" % (nameAccount.encode("utf-8"), token.encode("utf-8"))
    ExCommands(['powershell', 'yc init'], comm)
    print('Успех')
    menu()


def YcList():
    result = str(ExCommands(['powershell', 'yc config list --format yaml'], ''))
    print(result)
    token = str(*re.findall('(token: [0-9a-zA-Z_-]*)', result)).replace('token: ', '')
    print("Токен аккаунта:", token)
    menu()


def CreateKey1():
    global nameAccount
    if nameAccount == '':
        nameAccount = input('Введите имя аккаунта, который используете для управления облаком: ')
    print('Создание сервисного аккаунта yc-lab23')
    ExCommands(['powershell', 'yc iam service-account create --name yc-lab23'],'')
    ExCommands(['powershell', 'yc iam service-account add-access-binding --service-account-name yc-lab23 --name yc-lab23 --role admin'], '')
    idServiceAccount = GettingIDServiceAccount('yc-lab23')

    print('Получение id пользовательского аккаунта')
    login = input('Введите логин почты без @: ')
    resultTemp = ExCommands(['powershell', f'yc iam user-account get {login}'],'')
    print(resultTemp)
    idUserAccount = re.findall('id: \w*', resultTemp)[0].replace('id: ', '')
    print('ID пользовательского аккаунта: ', idUserAccount)

    ExCommands(['powershell', f'yc iam service-account add-access-binding {idServiceAccount} '
                              f'--role editor --subject userAccount:{idUserAccount}'], '')

    resultTemp = ExCommands(['powershell', 'yc config list'],'')
    idFolder = re.findall('folder-id: \w*', resultTemp)[0].replace('folder-id: ', '')

    ExCommands(['powershell', f'yc iam key create --service-account-name yc-lab23 --folder-id {idFolder} --output key.json'], '')

    ExCommands(['powershell', 'yc config profile create yc-lab23-profile'], '')
    ExCommands(['powershell', 'yc config set service-account-key key.json'], '')
    ExCommands(['powershell', f'yc config profile activate {nameAccount}'], '')
    resultTemp = ExCommands(['powershell', 'yc kms symmetric-key create --name key-lab23 --default-algorithm aes-256'], '')
    print(resultTemp)
    idKey = re.findall('key_id: \w*', resultTemp)[0].replace('key_id: ', '')
    ExCommands(['powershell', f'yc kms symmetric-key add-access-binding {idKey} --folder-id {idFolder} '
                              f'--role kms.admin --subject serviceAccount:{idServiceAccount}'], '')
    ExCommands(['powershell', 'yc config profile activate yc-lab23-profile'], '')
    ExCommands(['powershell', f'yc kms symmetric-key rotate --id {idKey} '], '')
    ExCommands(['powershell', f'yc config profile activate {nameAccount}'], '')
    ExCommands(['powershell', f'yc config profile delete yc-lab23-profile'], '')
    menu()

def CreateNetworkForVPN():
    ExCommands(['powershell', 'yc vpc network create --name vpn'], '')
    ExCommands(['powershell', 'yc vpc subnet create --name vpn-a --zone ru-central1-a --network-name vpn --range 192.168.0.0/24'], '')
    ExCommands(['powershell', 'yc vpc address create --external-ipv4 zone=ru-central1-a'], '')
    ExCommands(['powershell', 'yc vpc address create --external-ipv4 zone=ru-central1-a'], '')

    ip10_128 = input('Введите локальный IP машины в сети 10.128.0.0/24 ')
    ip192_168 = input('Введите локальный IP машины в сети 192.168.0.0/24 ')
    ExCommands(['powershell', 'yc vpc route-table create --name def-vpn --network-name default '
                              f'--route destination=192.168.0.0/24,next-hop={ip10_128}'], '')
    ExCommands(['powershell', 'yc vpc route-table create --name vpn-def --network-name vpn '
                              f'--route destination=10.128.0.0/24,next-hop={ip192_168}'], '')
    ExCommands(['powershell', 'yc vpc subnet update --name default-ru-central1-a --route-table-name def-vpn'], '')
    ExCommands(['powershell', 'yc vpc subnet update --name vpn-a --route-table-name vpn-def'], '')

    ip_def = input('Публичный IP ВМ в default сети: ')
    ip_vpn = input('Публичный IP ВМ в vpn сети: ')

    print(f'''
conn def-to-vpn
        authby=secret
        left=%defaultroute
        leftid={ip_def}
        leftsubnet=10.128.0.0/24
        right={ip_vpn}
        rightsubnet=192.168.0.0/24
        ike=aes256-sha2_256-modp1024!
        esp=aes256-sha2_256!
        keyingtries=0
        ikelifetime=1h
        lifetime=8h
        dpddelay=30
        dpdtimeout=120
        dpdaction=restart
        auto=start
''')

    print(f'''conn vpn-to-def
        authby=secret
        left=%defaultroute
        leftid={ip_vpn}
        leftsubnet=192.168.0.0/24
        right={ip_def}
        rightsubnet=10.128.0.0/24
        ike=aes256-sha2_256-modp1024!
        esp=aes256-sha2_256!
        keyingtries=0
        ikelifetime=1h
        lifetime=8h
        dpddelay=30
        dpdtimeout=120
        dpdaction=restart
        auto=start
''')

    print(f'{ip_def} {ip_vpn} : PSK "staratel"\n')
    print(f'{ip_vpn} {ip_def} : PSK "staratel"\n')
    menu()


def Create4VM():
    for i in ['5','20','50','100']:
        prog = f'yc compute instance create --name vm-{i} ' \
               '--create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2004-lts ' \
               f'--zone ru-central1-a --core-fraction {i} ' \
               '--network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 ' \
               f'--labels project=test{i}'
        ExCommands(['powershell', prog], '')
    menu()



def menu():
    init(autoreset=True)
    temp = input(   """Выбери пункт меню
    [0] Инициализация аккаунта (нужно имя и токен)
    [1] Создание ключа
    [2] Создание сетей и таблицы для 2 практики
    [3] Создание 4 ВМ 
    Введите число: """)

    if temp == "0":
        YcInitAccount()
    elif temp == "1":
        CreateKey1()
    elif temp == "2":
        CreateNetworkForVPN()
    elif temp == "3":
        Create4VM()
    elif temp == "4":
        YcList()

init(autoreset=True)
print(Fore.GREEN + """
███████╗████████╗ █████╗ ██████╗  █████╗ ████████╗███████╗██╗         ██████╗     ██████╗ ██╗   ██╗
██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██║         ╚════██╗   ██╔═████╗██║   ██║
███████╗   ██║   ███████║██████╔╝███████║   ██║   █████╗  ██║          █████╔╝   ██║██╔██║██║   ██║
╚════██║   ██║   ██╔══██║██╔══██╗██╔══██║   ██║   ██╔══╝  ██║          ╚═══██╗   ████╔╝██║╚██╗ ██╔╝
███████║   ██║   ██║  ██║██║  ██║██║  ██║   ██║   ███████╗███████╗    ██████╔╝██╗╚██████╔╝ ╚████╔╝ 
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚══════╝    ╚═════╝ ╚═╝ ╚═════╝   ╚═══╝  
""")
menu()
