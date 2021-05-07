# -*- coding: utf-8 -*-
import threading
import os
import socket
import sys

#Função para manter lista de frequências que um processo recebeu GRANT
def contar_frequencia(frequencias, pid_processo):
    if pid_processo in frequencias:
        frequencias[pid_processo] += 1
    else:
        frequencias[pid_processo] = 1

#Função de realizar conexão com um processo
def conectar_processo(coord, processos, opcao, n_processos):

    print("\nProcurando conexões...")
    coord.listen(n_processos)    #Número total de processos passado como parâmetro

    while opcao != '3':
        socket_processo, endereco_processo = coord.accept()
        print(f'\nConexão com {endereco_processo} foi estabelecida!')

        #Adiciona o socket do processo conectado no conjunto de processos
        processos.add(socket_processo)
    coord.close()

#Função para retornar o PID de um processo em uma mensagem
def retornar_pid(mensagem):
    inicio = mensagem.find('1|') + len('1|')
    fim = mensagem.find('|0')
    pid = mensagem[inicio:fim]

    return pid

#Algoritmo para realizar a exclusão mútua
def exclusao_mutua(processos, queue_exclusao, pids, frequencias, n_processos):

    #Espera todos sockets se conectarem
    while len(processos) != n_processos:
        continue

    while True:
        socket_processo = processos.pop()
        processos.add(socket_processo)

        #Evita que essa thread espere por mensagens de processos que já estão
        #na fila de exclusão mútua, esperando por um GRANT
        if socket_processo in queue_exclusao and socket_processo != queue_exclusao[0]:
            continue

        mensagem_recebida = socket_processo.recv(10).decode()

        if '1|' in mensagem_recebida[:2]:      #Se for uma mensagem de REQUEST
            pid_processo = retornar_pid(mensagem_recebida)

            #Se a fila de exclusão mútua estiver vazia, envia um GRANT imediatamente
            if not queue_exclusao:
                mensagem_envio = str('2|'+ str(os.getpid()) + '|').ljust(10,'0')
                socket_processo.send(mensagem_envio.encode('utf-8'))

                contar_frequencia(frequencias, pid_processo)

            pids.append(pid_processo)
            queue_exclusao.append(socket_processo)

        if '3|' in mensagem_recebida[:2]:        #Se for uma mensagem de RELEASE
            socket_processo = queue_exclusao.pop(0)
            pids.pop(0)

            #Se a fila de exclusão mútua não estiver vazia após o RELEASE,
            #envia um GRANT para o processo no início da fila
            if queue_exclusao:
                socket_processo = queue_exclusao[0]
                mensagem_envio = str('2|'+ str(os.getpid()) + '|').ljust(10,'0')
                socket_processo.send(mensagem_envio.encode('utf-8'))

                pid_processo = pids[0]
                contar_frequencia(frequencias, pid_processo)

#Função de interface
def interface(pids, frequencias, opcao):
    while True:
        print('\n\n'
              '| 1 - Imprimir a fila de pedidos atual\n'
              '| 2 - Imprimir lista de frequências de GRANTs por PID\n'
              '| 3 - Encerrar a execução do coordenador')
        opcao = input('\nInsira uma opção do menu: ')

        if opcao == '1':
            print('\n------------------------\n'
                    '     Fila de pedidos    \n'
                    '------------------------\n')
            print(pids)
        elif opcao == '2':
            print('\n------------------------\n'
                    '  Lista de frequências  \n'
                    '------------------------\n')
            print(frequencias)
        elif opcao == '3':
            print('\n------------------------\n'
                    '    Encerrar execução   \n'
                    '------------------------\n')
            break
        else:
            print('\nInsira uma opção válida!')

if __name__ == '__main__':
    HOST = socket.gethostname()
    PORT = 63640

    #Criando o socket do Coordenador
    socket_coord = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_coord.bind((HOST, PORT))
    print('\nO socket do Coordenador foi criado!')

    #Conjunto de processos, fila de exclusão mútua,
    #fila de PIDs e lista de frequências de GRANTs
    conjunto_processos = set()
    fila_exclusao = []
    fila_pids = []
    lista_frequencias = {}
    opcao_menu = ''

    #Variáveis para avaliação
    N = 2

    #Definindo as threads e suas respectivas funções
    t1 = threading.Thread(target=conectar_processo,
                          args=(socket_coord, conjunto_processos, opcao_menu, N))
    t2 = threading.Thread(target=exclusao_mutua,
                          args=(conjunto_processos, fila_exclusao, fila_pids, lista_frequencias, N))
    t3 = threading.Thread(target=interface, args=(fila_pids, lista_frequencias, opcao_menu))

    #As threads terminarão ao encerrar a execução do coordenador
    t1.daemon=True
    t2.daemon=True
    t3.daemon=True

    #Iniciando as threads
    t1.start()
    t2.start()

    #Inicia a thread com a interface assim que todos os sockets forem conectados
    #para que o menu não fique perdido em meio às mensagens de êxito de conexão
    while len(conjunto_processos) != N:
        continue

    t3.start()

    #O código abaixo do join só será executado quando a thread 3 terminar
    #Para isso, o usuário deve digitar '3'
    t3.join()

    print('Encerrando conexão...')
    print('Conexão encerrada...')
    print('\nFim da execução do coordenador...')
    sys.exit()
