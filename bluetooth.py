#!/usr/bin/env python3
import subprocess
import serial

class BlueComm:
    def __init__(self):
        self.porta = serial.Serial('/dev/ttySOFT0', baudrate=9600, timeout=1)
        
    def read_serial(self):
        res = self.porta.read(1024) 
        if len(res):
            return self._decodificar(res.splitlines())
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
        
        if len(text):
            self.porta.write(bytes(text, 'utf-8'))

class BlueControl:

    def __init__(self):
        self.shell = ShellExec()

    def exec_command(self, comm):
        retorno = ''
        if comm[1] == 'start' and comm[2] == 'monitor_gps':
            lst_comm = ['sudo', 'systemctl', 'start', 'monitor_gps.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[1] == 'stop' and comm[2] == 'monitor_gps':
            lst_comm = ['sudo', 'systemctl', 'stop', 'monitor_gps.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[1] == 'start' and comm[2] == 'monitor_ignicao':
            lst_comm = ['sudo', 'systemctl', 'start', 'monitor_ignicao.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[1] == 'stop' and comm[2] == 'monitor_ignicao':
            lst_comm = ['sudo', 'systemctl', 'stop', 'monitor_ignicao.service']
            retorno = self.shell.executar(lst_comm)
        elif comm[1] == 'wifi':
            self.config_wifi(comm)

        return retorno

    def config_wifi(comm):
        parar_wifi = ['sudo', 'killall', 'wpa_supplicant']
        self.shell.executar(parar_wifi)
        config = ['sudo', 'wpa_passphrase', comm[2], comm[3], '|','sudo', 'tee', '/etc/wpa_supplicant.conf']
        self.shell.executar(config)
        up_wifi = ['sudo', 'wpa_supplicant', '-c', '/etc/wpa_supplicant.conf', '-i', 'wlan0']
        self.shell.executar(up_wifi)
        return 'wifi configurado'

            
class ShellExec:
            
    def __init__(self):
        self.comando = None
        
    def executar(self, comm):
        output = []
        if self._check(comm):
            self.comando = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
            output, errors = self.comando.communicate()
        
        return output

    def _check(self, comm):
        retorno = True
        if comm[0] == '+DISC:SUCCESS':
            retorno = False

        return retorno
        

def main():
    bluec = BlueControl()
    shell = ShellExec()
    bluet = BlueComm()
    while True:
        comando = bluet.read_serial()
        if len(comando):
            print('comando: '+str(comando))
            if comando[0] == 'cmd':
                retorno = bluec.exec_command(comando)
                bluet.send_serial(retorno)
                print('retorno: '+ retorno)
            else:
                saida = shell.executar(comando)
                print('saida: '+str(saida))
                bluet.send_serial(saida)
        
        
if __name__ == "__main__":
    main()
