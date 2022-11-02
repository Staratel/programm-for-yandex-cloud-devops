"""Программа-скрипт для ускоренного выполнения заданий по
курсу Инженер компьютерных систем
"""


import re
import subprocess


def ExCommands(textComands, communic):
    """Возвращает результат выполнения команды в PowerShell
    :param textComands: строка команды
    :param communic: строка ввода в консоль
    :return результат выполнения команды
    """
    return subprocess.Popen(textComands, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate(communic)


def YcInitAccount(name:str, token:str):
    """Инициализирует аккаунт в системе
    :param name: имя аккаунта
    :param token: OAth token"""
    comm = b"2\n%b\n%b\n1\n\n2\n" % (name, token)
    ExCommands(['powershell', 'yc init'],comm)
    print('Успех')
    menu()


def YcList():
    """Печатает информацию и отдельно токен активного аккаунта"""
    result = str(ExCommands(['powershell', 'yc config list --format yaml'],''))
    print(result)
    token = str(*re.findall('(token: [0-9a-zA-Z_-]*)', result)).replace('token: ', '')
    print("Токен аккаунта:",token)
    menu()


def CreateSpecification():
    result = str(ExCommands(['powershell', 'yc vpc network get --name my-network'],''))
    name = str(*re.findall('(name: \w*-\w*)', result)).replace('name: ','')
    idNetwork = str(*re.findall('\'id: \w*', result)).replace('\'id: ','')
    print('ID сети [%s] и его имя [%s] ' % (idNetwork,name))

    result = str(ExCommands(['powershell', 'yc iam service-account list --format yaml'],''))
    idServiceAccount = re.findall('- id: \w*', result)[0].replace('- id: ','')
    print('Идентификатор сервисного аккаунта [%s]' % idServiceAccount)

    text=("""name: my-group
service_account_id: %s
 
instance_template:
    platform_id: standard-v1
    resources_spec:
        memory: 2g
        cores: 2
    boot_disk_spec:
        mode: READ_WRITE
        disk_spec:
            image_id: fd8kpq7jt2i4vkhse3s1
            type_id: network-hdd
            size: 32g
    network_interface_specs:
        - network_id: %s
          primary_v4_address_spec: { one_to_one_nat_spec: { ip_version: IPV4 }}
    scheduling_policy:
        preemptible: false
    metadata:
      user-data: |-
        #cloud-config
          package_update: true
          runcmd:
            - [ apt-get, install, -y, nginx ]
            - [/bin/bash, -c, 'source /etc/lsb-release; sed -i "s/Welcome to nginx/It is $(hostname) on $DISTRIB_DESCRIPTION/" /var/www/html/index.nginx-debian.html']
 
deploy_policy:
    max_unavailable: 1
    max_expansion: 0
scale_policy:
    fixed_scale:
        size: 3
allocation_policy:
    zones:
        - zone_id: ru-central1-a
 
load_balancer_spec:
    target_group_spec:
        name: my-target-group             """ % (idServiceAccount,idNetwork))

    file = open('specification.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл со старым образом успешно перезаписан')

    #Создаём группу виртуальных машин
    ExCommands(['powershell', 'yc compute instance-group create --file specification.yaml'], '')
    input('Техническая пауза, делай скриншот результата команд из Notion. После этого будет создание балансёра')
    CreateNetworkLoadBalancer()

    input('Техническая пауза, делай скриншот результата команд из Notion. После этого будет переписан образ на новый')
    text = ("""name: my-group
service_account_id: %s

instance_template:
    platform_id: standard-v1
    resources_spec:
        memory: 2g
        cores: 2
    boot_disk_spec:
        mode: READ_WRITE
        disk_spec:
            image_id: fd87uq4tagjupcnm376a 
            type_id: network-hdd
            size: 32g
    network_interface_specs:
        - network_id: %s
          primary_v4_address_spec: { one_to_one_nat_spec: { ip_version: IPV4 }}
    scheduling_policy:
        preemptible: false
    metadata:
      user-data: |-
        #cloud-config
          package_update: true
          runcmd:
            - [ apt-get, install, -y, nginx ]
            - [/bin/bash, -c, 'source /etc/lsb-release; sed -i "s/Welcome to nginx/It is $(hostname) on $DISTRIB_DESCRIPTION/" /var/www/html/index.nginx-debian.html']

deploy_policy:
    max_unavailable: 1
    max_expansion: 0
scale_policy:
    fixed_scale:
        size: 3
allocation_policy:
    zones:
        - zone_id: ru-central1-a

load_balancer_spec:
    target_group_spec:
        name: my-target-group""" % (idServiceAccount, idNetwork))

    file = open('specification.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл с новым образом успешно перезаписан')

    # Обновляем группу виртуальных машин
    ExCommands(['powershell', 'yc compute instance-group update --name my-group --file specification.yaml'], '')

    menu()


def CreateNetworkLoadBalancer():
    prog_config = ['powershell', ' yc load-balancer network-load-balancer create --region-id ru-central1 --name my-load-balancer --listener name=my-listener,external-ip-version=ipv4,port=80']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).wait()

    prog_config = ['powershell', ' yc load-balancer nlb list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idNetworkLoadBalancer = str(*re.findall('- id: \w*', result)).replace('- id: ','')
    print('ИД балансёра [%s]' % idNetworkLoadBalancer)

    prog_config = ['powershell', ' yc load-balancer target-group list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idTargetGroup = str(*re.findall('- id: \w*', result)).replace('- id: ','')
    print('ИД целевой группы [%s]' % idTargetGroup)

    prog_config = ['powershell', ' yc load-balancer network-load-balancer attach-target-group %s --target-group target-group-id=%s,healthcheck-name=test-health-check,healthcheck-interval=2s,healthcheck-timeout=1s,healthcheck-unhealthythreshold=2,healthcheck-healthythreshold=2,healthcheck-http-port=80'%(idNetworkLoadBalancer,idTargetGroup)]
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())


def CreatePackerSpecification():
    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    token = str(*re.findall('(token: [0-9a-zA-Z_-]*)', result)).replace('token: ', '')
    idFolder = str(*re.findall('folder-id: \w*', result)).replace('folder-id: ', '')

    print('ИД Каталога [%s] и токен [%s] ' % (idFolder, token))

    prog_config = ['powershell', 'yc vpc subnet list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idSubnet = str(re.findall('(- id: \w*)', result)[0]).replace('- id: ', '')
    idZone = str(re.findall('(zone_id: \w*-\w*-\w*)', result)[0]).replace('zone_id: ', '')
    print(idSubnet, idZone)

    text = ('''source "yandex" "ubuntu-nginx" {
  token               = "%s"
  folder_id           = "%s"
  source_image_family = "ubuntu-2004-lts"
  ssh_username        = "ubuntu"
  use_ipv4_nat        = "true"
  image_description   = "my custom ubuntu with nginx"
  image_family        = "ubuntu-2004-lts"
  image_name          = "my-ubuntu-nginx"
  subnet_id           = "%s"
  disk_type           = "network-ssd"
  zone                = "%s"
}

build {
  sources = ["source.yandex.ubuntu-nginx"]

  provisioner "shell" {
    inline = ["sudo apt-get update -y",
              "sudo apt-get install -y nginx",
              "sudo systemctl enable nginx.service"
             ]
  }
}''') % (token,idFolder,idSubnet,idZone)

    file = open('my-ubuntu-nginx.pkr.hcl', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    menu()


def CreateTerraformSpecification():
    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    token = str(*re.findall('(token: [0-9a-zA-Z_-]*)', result)).replace('token: ', '')
    idCloud = str(*re.findall('cloud-id: \w*', result)).replace('cloud-id: ', '')
    idFolder = str(*re.findall('folder-id: \w*', result)).replace('folder-id: ', '')

    print('ИД Каталога [%s], облака [%s] и токен [%s] ' % (idFolder,idCloud, token))

    text = ('''terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
}
 
provider "yandex" {
  token  =  "%s"
  cloud_id  = "%s"
  folder_id = "%s"
  zone      = "ru-central1-a"
}
 
resource "yandex_compute_instance" "vm-1" {
  name = "from-terraform-vm"
  platform_id = "standard-v1"
  zone = "ru-central1-a"
 
  resources {
    cores  = 2
    memory = 2
  }
 
  boot_disk {
    initialize_params {
      image_id = "fd8kpq7jt2i4vkhse3s1"
    }
  }
 
  network_interface {
    subnet_id = yandex_vpc_subnet.subnet-1.id
    nat       = true
  }
 
  metadata = {
    ssh-keys = "ubuntu:${file("~/.ssh/id_rsa.pub")}"
  }
}
 
resource "yandex_vpc_network" "network-1" {
  name = "from-terraform-network"
}
 
resource "yandex_vpc_subnet" "subnet-1" {
  name           = "from-terraform-subnet"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network-1.id
  v4_cidr_blocks = ["10.2.0.0/16"]
}
 
resource "yandex_mdb_postgresql_cluster" "postgres-1" {
  name        = "postgres-1"
  environment = "PRESTABLE"
  network_id  = yandex_vpc_network.network-1.id
 
  config {
    version = 12
    resources {
      resource_preset_id = "s2.micro"
      disk_type_id       = "network-ssd"
      disk_size          = 16
    }
    postgresql_config = {
      max_connections                   = 395
      enable_parallel_hash              = true
      vacuum_cleanup_index_scale_factor = 0.2
      autovacuum_vacuum_scale_factor    = 0.34
      default_transaction_isolation     = "TRANSACTION_ISOLATION_READ_COMMITTED"
      shared_preload_libraries          = "SHARED_PRELOAD_LIBRARIES_AUTO_EXPLAIN,SHARED_PRELOAD_LIBRARIES_PG_HINT_PLAN"
    }
  }
 
  database {
    name  = "postgres-1"
    owner = "my-name"
  }
 
  user {
    name       = "my-name"
    password   = "Test1234"
    conn_limit = 50
    permission {
      database_name = "postgres-1"
    }
    settings = {
      default_transaction_isolation = "read committed"
      log_min_duration_statement    = 5000
    }
  }
 
  host {
    zone      = "ru-central1-a"
    subnet_id = yandex_vpc_subnet.subnet-1.id
  }
}
 
output "internal_ip_address_vm_1" {
  value = yandex_compute_instance.vm-1.network_interface.0.ip_address
}
 
output "external_ip_address_vm_1" {
  value = yandex_compute_instance.vm-1.network_interface.0.nat_ip_address
}''') % (token, idCloud, idFolder)

    file = open('my-config.tf', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    menu()


def CreateKubectlSpecification():
    prog_config = ['powershell', 'yc container img list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idImage = str(*re.findall('(name: \w*/\w*-\w*)', result)).replace('name: ', '')
    print(idImage)

    text = ('''apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-nginx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: cr.yandex/%s''') % (idImage)


    file = open('my-nginx.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    menu()


def CreateSpecification2():
    prog_config = ['powershell', 'yc vpc network get --name default']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idNetwork = str(*re.findall('\'id: \w*', result)).replace('\'id: ', '')
    print('ID сети [%s]' % idNetwork)

    prog_config = ['powershell', 'yc iam service-account list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idServiceAccount = re.findall('- id: \w*', result)[0].replace('- id: ', '')
    print('Идентификатор сервисного аккаунта [%s]' % idServiceAccount)

    subnets = []
    for let in 'abc':
        prog_config = ['powershell', f'yc vpc subnet get --name default-ru-central1-{let}']
        result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
        subnet = re.findall('\'id: \w*', result)[0]
        subnets.append(subnet.replace('\'id: ', ''))
    print(subnets)

    text = ('''name: my-group
service_account_id: %s
 
instance_template:
    platform_id: standard-v1
    resources_spec:
        memory: 2g
        cores: 2
    boot_disk_spec:
        mode: READ_WRITE
        disk_spec:
            image_id: fd8fosbegvnhj5haiuoq 
            type_id: network-hdd
            size: 32g
    network_interface_specs:
        - network_id: %s
          subnet_ids: 
            - %s
            - %s
            - %s
          primary_v4_address_spec: { one_to_one_nat_spec: { ip_version: IPV4 }}
    scheduling_policy:
        preemptible: false
    metadata:
      user-data: |-
        #cloud-config
        users:
          - name: my-user
            groups: sudo
            lock_passwd: true
            sudo: 'ALL=(ALL) NOPASSWD:ALL'
            ssh-authorized-keys:
              - ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCMjt7WavaBl9ewKhpGq8zFhv/MbkjT5Cl4o5J7+yaP0GZ+iO5bJ45b1c5GWWzyCadXTdbsrsmHo6iXvg3p1tM65yrywSozZ5C4NZOen8cuOMDkHe37LYgJx7kXqFlTDWZsRl4yCY47OTQ4mP9IJIn3EaQHRM0nPY61RmYKA7fI9UXarWijo9b2DC8qy2fmvb3iR7pIwf7ncdywbJwbiRe9t8i2m50RFpZZosy3D35dE2TWelrcXvZV4kLPFgEv8KiCbO60jM0gR5qHAniFoZY0DWIAn9Vc4KexrKi4L8blGl6fD5B0UwDmpC+6w+hUJQf6VDODDmKNLB8w/O2v+xLJ rsa-key-20220329
        package_update: true
        runcmd:
          - [ apt-get, install, -y, nginx ]
          - [/bin/bash, -c, 'source /etc/lsb-release; sed -i "s/Welcome to nginx/It is $(hostname) on $DISTRIB_DESCRIPTION/" /var/www/html/index.nginx-debian.html']
 
deploy_policy:
    max_unavailable: 1
    max_expansion: 0
scale_policy:
    fixed_scale:
        size: 3
allocation_policy:
    zones:
        - zone_id: ru-central1-a
        - zone_id: ru-central1-b
        - zone_id: ru-central1-c
 
load_balancer_spec:
    target_group_spec:
        name: my-target-group''') % (idServiceAccount,idNetwork,subnets[0],subnets[1],subnets[2])

    file = open('specification.yaml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    prog_config = ['powershell', 'yc compute instance-group create --file specification.yaml']
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    result = str(ExCommands(['powershell', 'yc load-balancer tg get --name my-target-group'], ''))
    targetGroupId = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    print('Создание балансёра',targetGroupId)
    prog_config = ['powershell', 'yc load-balancer network-load-balancer create --region-id ru-central1 --name my-load-balancer '
                                 '--listener name=my-listener,external-ip-version=ipv4,port=80 '
                                 f'--target-group target-group-id={targetGroupId},'
                                 'healthcheck-name=test-health-check,healthcheck-interval=2s,'
                                 'healthcheck-timeout=1s,healthcheck-unhealthythreshold=2,'
                                 'healthcheck-healthythreshold=2,healthcheck-http-port=80'
                                 ]
    subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate()

    result = str(ExCommands(['powershell', 'yc compute instance-group get --name my-group'],''))
    instanceGroupId = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')
    result = str(ExCommands(['powershell', 'yc load-balancer nlb get --name my-load-balancer'], ''))
    balancerId = re.findall('\'id: \w*', result)[0].replace('\'id: ', '')

    print(f'while true; do yc compute instance-group --id {instanceGroupId} list-instances; yc load-balancer network-load-balancer --id {balancerId} target-states --target-group-id {targetGroupId}; sleep 5; done')
    menu()


def CreateConfig():
    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFolder = str(*re.findall('folder-id: \w*', result)).replace('folder-id: ', '')

    text = ('''status:
   port: "16241"
 
storages:
   - name: main
     plugin: fs
     config:
       directory: /var/lib/yandex/unified_agent/main
       max_partition_size: 100mb
       max_segment_size: 10mb
 
channels:
   - name: cloud_monitoring
     channel:
       pipe:
         - storage_ref:
             name: main
       output:
         plugin: yc_metrics
         config:
           folder_id: "%s"
           iam:
             cloud_meta: {}
 
routes:
   - input:
       plugin: linux_metrics
       config:
         namespace: sys
     channel:
       channel_ref:
         name: cloud_monitoring
 
   - input:
       plugin: agent_metrics
       config:
         namespace: ua
     channel:
       pipe:
         - filter:
             plugin: filter_metrics
             config:
               match: "{scope=health}"
       channel_ref:
         name: cloud_monitoring
 
import:
   - /etc/yandex/unified_agent/conf.d/*.yml''') % (idFolder)

    file = open('config.yml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')

    menu()


def CreatingConfigProm():
    prog_config = ['powershell', 'yc config list --format yaml']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    idFolder = str(*re.findall('folder-id: \w*', result)).replace('folder-id: ', '')

    prog_config = ['powershell', 'yc iam api-key create --service-account-name test']
    result = str(subprocess.Popen(prog_config, stdin=subprocess.PIPE, stdout=subprocess.PIPE).communicate())
    secretToken = str(*re.findall('secret: [0-9a-zA-Z_-]*', result)).replace('secret: ', '')

    print(idFolder, secretToken)

    text = ('''global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).
 
rule_files:
 
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']
 
  - job_name: 'yc-monitoring-export'
    metrics_path: '/monitoring/v2/prometheusMetrics'
    params:
      folderId:
      - '%s'
      service:
      - 'storage' 
    bearer_token: '%s'
    static_configs:
    - targets: ['monitoring.api.cloud.yandex.net']
      labels:
          folderId: '%s'
          service: 'storage' ''') % (idFolder, secretToken,idFolder)

    file = open('prometheus.yml', "w+")
    file.write(text)
    file.close()
    print('Файл успешно перезаписан')


def menu():
    temp = input(
"""Выбери пункт меню
[1] Инициализация аккаунта (нужно имя и токен)
[2] Просмотр данных аккаунта, сетей и вм
[3] Создание файла спецификации specification.yaml и балансёра
[5] Создание спецификации для Пакера
[6] Создание спецификации для Терраформ
[7] Создание спецификации для kubectl
[8] Создание второй спецификации specification.yaml
[9] Создание конфигурации config.yml
[10] Создание конфигурации prometheus.yml
Введите число: """)

    if temp == "1":
        name, token = input("Введите имя, токен через пробел: ").split(" ")
        YcInitAccount(name.encode("utf-8"), token.encode("utf-8"))
    elif temp == "2":
        YcList()
    elif temp == "3":
        CreateSpecification()
    elif temp == "5":
        CreatePackerSpecification()
    elif temp == "6":
        CreateTerraformSpecification()
    elif temp == "7":
        CreateKubectlSpecification()
    elif temp == "8":
        CreateSpecification2()
    elif temp == "9":
        CreateConfig()
    elif temp == "10":
        CreatingConfigProm()

print("hello")
menu()