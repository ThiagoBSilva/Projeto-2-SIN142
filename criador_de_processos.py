# -*- coding: utf-8 -*-
from datetime import datetime
import multiprocessing
import os
import socket
import time
import sys

#Função para escrever registro no arquivo
def escrever(segundos):
    with open('resultado.txt', 'a') as arquivo:
        horario_atual = datetime.now()
        registro = (str(os.getpid())+': '+datetime.strftime(horario_atual, '%H:%M:%S.%f')+'\n')

        arquivo.write(registro)
        time.sleep(segundos)
        arquivo.close()

#Função para executar um processo
def executar_processo(repeticoes, tempo):
    host = socket.gethostbyname(socket.gethostname())
    port = 63640

    socket_processo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_processo.connect((host, port))

    endereco_coord = socket_processo.getpeername()
    print(f'\nConexão com {endereco_coord} foi estabelecida!')

    #Envia a mensagem de REQUEST, espera um GRANT. Ao recebê-lo, escreve a hora atual
    #no arquivo e devolve uma mensagem de RELEASE
    while repeticoes > 0:
        mensagem_envio = str('1|' + str(os.getpid()) + '|').ljust(10,'0')
        socket_processo.send(mensagem_envio.encode('utf-8'))

        mensagem_recebida = socket_processo.recv(10).decode()
        if '2|' in mensagem_recebida[:2]:
            escrever(tempo)

        mensagem_envio = str('3|' + str(os.getpid()) + '|').ljust(10,'0')
        socket_processo.send(mensagem_envio.encode('utf-8'))

        repeticoes -= 1
    print(f'\nProcesso {os.getpid()} finalizado.')
    socket_processo.close()

if __name__ == '__main__':

    #Variável para avaliação
    N = 2       #Número de processos a serem criados
    R = 10      #Repetições
    K = 3       #Tempo na função sleep()
    processos = []

    for _ in range(N):
        processo = multiprocessing.Process(target=executar_processo, args=(R, K))
        processo.start()
        processos.append(processo)

    for processo in processos:
        processo.join()

    for processo in processos:
        processo.terminate()

    print('\nFim da execução dos processos...')
    sys.exit()
