#!/usr/bin/env python3
import subprocess
import serial, os, io
from time import sleep
import threading

class BlueComm:
    def __init__(self):
        self.porta = serial.Serial('/dev/ttySOFT0', baudrate=9600, timeout=1)
        
    def read_serial(self):
        res = self.porta.read(1024) 
        if len(res):
            return res.decode('utf-8')
        else:
            return []

    def _decodificar(self, res):
        nova_lista = []

        for linha in res:
            split = linha.decode('utf-8').split(' ')

            for s in split:
                nova_lista.append(s)

        return nova_lista

            
    def send_serial(self, text):
        #print('send_serial: '+text)        
        if len(text):
            self.porta.write(str(text).encode('utf-8'))

class BlueControl:

    def __init__(self):
        self.shell = ShellExec()
        self.essids = dict()

    def exec_command(self, comm):
        print('exec_command'+str(comm))
        retorno = ''
        if comm[0] == 'start' and comm[1] == 'monitor_gps\r\n':
            lst_comm = ['sudo', 'systemctl', 'start', 'monitor_gps.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[0] == 'stop' and comm[1] == 'monitor_gps\r\n':
            lst_comm = ['sudo', 'systemctl', 'stop', 'monitor_gps.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[0] == 'start' and comm[1] == 'monitor_ignicao\r\n':
            lst_comm = ['sudo', 'systemctl', 'start', 'monitor_ignicao.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[0] == 'stop' and comm[1] == 'monitor_ignicao\r\n':
            lst_comm = ['sudo', 'systemctl', 'stop', 'monitor_ignicao.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[0] == 'wifi' and comm[1] == "scan\r\n":
            self.essids = self.shell.get_essid()           
            retorno = self.essids
        elif comm[0] == 'wifi' and comm[1] == 'conn':
            if len(self.essids) > 0:
                try:
                    num_essid = int(comm[2])
                    senha = comm[3].rstrip('\n')
                    senha = senha.rstrip('\r')
                    retorno = self.shell.config_wifi(self.essids[num_essid], senha)
                except ValueError:
                    retorno = 'Numero da rede wifi invalido'
            else:
                retorno = 'Execute wifi scan primeiro e selecione uma rede'

        elif comm[0] == 'wifi' and comm[1] == 'up\r\n':
            self.shell.up_interface()
            retorno = 'Ok'
        elif comm[0] == 'wifi' and comm[1] == 'down\r\n':
            self.shell.down_interface()
            retorno = 'Ok'
        elif comm[0] == 'wifi' and comm[1] == 'status\r\n':
            retorno = self.shell.wifi_status()
        elif comm[0] == 'servicos' and comm[1] == 'status\r\n':
            retorno = self.shell.service_status()
        else:
            retorno = 'comando nao encontrado'

        return retorno

            
class ShellExec:
            
    def __init__(self):
        self.comando = None
        self.essid = ''
        
    def executar(self, comm):
        output = []
        if self._check(comm):
            self.comando = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
            output, errors = self.comando.communicate()
        
        return 'Ok'

    def config_wifi(self, essid, psk):
        os.system('sudo killall wpa_supplicant')
        sleep(2)
        self.add_config_network(essid, psk)
        os.system('sudo wpa_supplicant -B -c /etc/wpa_supplicant/wpa_supplicant.conf -i wlan0')

        return 'wifi configurado'


    def up_interface(self):
        os.system('sudo ip link set wlan0 up')
        sleep(2)

    def down_interface(self):
        os.system('sudo ip link set wlan0 down')
        sleep(2)

    def get_essid(self):
        os.system('sudo ip link set wlan0 up')
        sleep(2)
        terminal = os.popen('iwlist wlan0 scan | grep ESSID')
        saida = terminal.read()
        buf = io.StringIO(saida)
        contador = 1
        self.essid = dict()
        for linha in buf:
            s = linha.strip().split(":")
            self.essid[contador] = s[1].replace('"','')
            contador = contador + 1
            
        return self.essid

    def add_config_network(self, essid, psk):
        network='\nnetwork={\nssid=\"#essid\" \npsk=\"#psk\" \n}'
        network = network.replace('#essid', essid)
        network = network.replace('#psk', psk)
        print(network)
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as arquivo:
            arquivo.write(network)
            arquivo.flush()
            arquivo.close()

    def wifi_status(self):
        saida = os.popen('iwconfig wlan0')
        texto = saida.read()

        posicao = texto.find('ESSID:')
        essid = ''
        if posicao != -1:
            posicao = posicao + 7
            loop = True
            while loop:
                essid = essid + texto[posicao]
                posicao = posicao + 1
                if texto[posicao] == '"':
                    loop = False
            essid = 'Conectado a: ' + essid
        else:
            essid = 'Nao Conectado'

        return essid

    def service_status(self):
        texto_saida = self.saida_shell('systemctl status monitor_gps')
        posicao = texto_saida.find('Active:')
        posicao = posicao + 8

        resumo_status = dict()
        loop = True
        status = ''
        while loop:
            if texto_saida[posicao] != ' ':
                status = status + texto_saida[posicao]
                posicao = posicao + 1
            else:
                loop = False

        resumo_status['monitor_gps'] = status

        texto_saida = self.saida_shell('systemctl status monitor_ignicao')
        posicao = texto_saida.find('Active:')
        posicao = posicao + 8

        loop = True
        status = ''

        while loop:
            if texto_saida[posicao] != ' ':
                status = status + texto_saida[posicao]
                posicao = posicao + 1
            else:
                loop = False
        
        resumo_status['monitor_ignicao'] = status

        print('Resumo status: '+str(resumo_status))
        
        return str(resumo_status)

    

    def _check(self, comm):
        retorno = True
        if comm[0] == '+DISC:SUCCESS':
            retorno = False

        return retorno

    def saida_shell(self, comando):
        saida = os.popen(comando)

        return saida.read()
        


def main():
    bluec = BlueControl()
    shell = ShellExec()
    bluet = BlueComm()
    while True:
        #print('loop')
        comando = bluet.read_serial()
        if len(comando):            
            retorno = bluec.exec_command(comando.split(" "))
            bluet.send_serial(retorno)
            print('retorno: '+ str(retorno))

        sleep(2)
thread = threading.Thread(target=main)
thread.start()

