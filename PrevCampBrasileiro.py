# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 18:38:51 2021

@author: Tomas Pegado
"""

# Importando as bibliotecas
import requests 
import pandas as pd 
import json 
import numpy as np
import random

##################################

# Importando e limpando os dados

## Parametros 
## Chaves
live = 'live_0c4bb3b9bb64403be363456befefe8'
autho = {'Authorization': f'Bearer {live}'}
df2 = pd.DataFrame()
times = dict()
rod_total = pd.DataFrame()
rod = pd.DataFrame()

# Função para importar os dados
def dados_import():
    ## Campeonato 
    campeonato = {'campeonato-brasileiro':10}
    campeonato_id = campeonato['campeonato-brasileiro']

    ## Importando dados da API 
    ## Tabela
    tab = requests.get(f'https://api.api-futebol.com.br/v1/campeonatos/{campeonato_id}/tabela',headers=autho)

    ## Lendo os dados da tabela do campeonato 
    t = tab.json()

    ## Dataframe da tabela atualizada do Brasileirão
    df2 = pd.DataFrame.from_dict(t)
    df2 = df2.drop(columns=['variacao_posicao','ultimos_jogos'])

    ## Dict com os nomes e os ids dos times
    for j in range(0,20):
        i = df2['time'][j]['time_id']
        n = df2['time'][j]['nome_popular']
        times[n]=i


    ## limpando os dados da coluna time
    for j in range(len(df2)):
        df2['time'][j] = df2['time'][j]['nome_popular']
        
    ## Pegando os dados da rodada1
    rod1 = requests.get(f'https://api.api-futebol.com.br/v1/campeonatos/{campeonato_id}/rodadas/1',headers=autho)
    rod1 = rod1.json()

    ## Criando o Dataframe da rodada 1
    rod1s = pd.Series(rod1)
    rod1df = pd.DataFrame.from_dict(rod1s['partidas']).drop(columns = ['campeonato','status','slug','data_realizacao','hora_realizacao','data_realizacao_iso', 'estadio','_link'])
    for j in range(len(rod1df)):
        rod1df['time_mandante'][j] = rod1df['time_mandante'][j]['nome_popular']
        rod1df['time_visitante'][j] = rod1df['time_visitante'][j]['nome_popular']


    ## Criando o Dataframe pro restante das rodadas
    rod_total = pd.DataFrame(columns = rod1df.columns)
    for rodada in range(1,39):
        
        rodn = requests.get(f'https://api.api-futebol.com.br/v1/campeonatos/{campeonato_id}/rodadas/{rodada}',headers=autho)
        rodn = rodn.json()
        rodns = pd.Series(rodn)
        rodndf = pd.DataFrame.from_dict(rodns['partidas']).drop(columns=['campeonato','status','slug','data_realizacao','hora_realizacao','data_realizacao_iso', 'estadio','_link'])
        
        for j in range(len(rodndf)):
            rodndf['time_mandante'][j] = rodndf['time_mandante'][j]['nome_popular']
            rodndf['time_visitante'][j] = rodndf['time_visitante'][j]['nome_popular']
        
        frames = [rod_total, rodndf]
        rod_total = pd.concat(frames)
    rod_total=rod_total.drop(columns=['partida_id','placar'])

    ## tirando as linhas das partidas que ainda não aconteceram
    rod = rod_total.copy()
    rod=rod.dropna()

    ## Criando coluna de qual time ganhou ou se deu empate
    rod.loc[rod.placar_mandante>rod.placar_visitante, 'resultado'] = 'M'
    rod.loc[rod.placar_mandante==rod.placar_visitante, 'resultado'] = 'E'
    rod.loc[rod.placar_mandante<rod.placar_visitante, 'resultado'] = 'V'
        

    rod=rod.reset_index()
    rod=rod.drop(columns=['index'])

    ## tirando as linhas das partidas que ainda não aconteceram
    rod=rod.dropna()

dados_import()
####################################

# Construindo os vetores de probabilidade

## Parametro
dict_P = dict()

## Função que retorna os vetores de probabilidade até a rodada atual do campeonato  
def prob_vectors():

    ## Criando dicionario de Probabilidade do inicio do campeonato
    for time in times:
        dict_P[time] = {'PC':np.array([1/3,1/3,1/3]),'PF':np.array([1/3,1/3,1/3]),'r':0}   

    ## funcao para definir o rendimento do time
    def rend(time, partida=0):
        
        jogos = 0
        pontos = 0    
        for i in range(partida):
            if rod['time_mandante'][i] == time:
                jogos+=1
                if rod['resultado'][i] =='M':
                    pontos+=3
                elif rod['resultado'][i] == 'E':
                    pontos+=1
            if rod['time_visitante'][i] == time:
                jogos+=1
                if rod['resultado'][i] =='V':
                    pontos+=3
                elif rod['resultado'][i] =='E':
                    pontos+=1
        if jogos == 0:
            dict_P[time]['r'] = 0
            return dict_P[time]['r']
        
        dict_P[time]['r']=pontos/(jogos*3)
        return dict_P[time]['r']


    ## Codigo para calcular os vetores de Probabilidade
    p = 5
    for partida in range(len(rod)):
        
        if rod['resultado'][partida] == 'M':        
            mandante = rod['time_mandante'][partida]
            visitante = rod['time_visitante'][partida]
            rm = rend(mandante,partida)
            rv = rend(visitante,partida)
            
            PC = dict_P[mandante]['PC']
            PC = (p*PC + rv*np.array([1,0,0]))/(p + rv)
            dict_P[mandante]['PC'] = PC
            
            PF = dict_P[visitante]['PF']
            PF = (p*PF + (1-rm)*np.array([0,0,1]))/(p + (1 - rm))
            dict_P[visitante]['PF'] = PF
        
        elif rod['resultado'][partida] == 'V':
            mandante = rod['time_mandante'][partida]
            visitante = rod['time_visitante'][partida]
            rm = rend(mandante,partida)
            rv = rend(visitante,partida)
            
            PF = dict_P[visitante]['PF']
            PF = (p*PF + rm*np.array([1,0,0]))/(p + rm)
            dict_P[visitante]['PF'] = PF
            
            PC = dict_P[mandante]['PC']
            PC = (p*PF + (1-rv)*np.array([0,0,1]))/(p + (1 - rv))
            dict_P[mandante]['PC'] = PC
        
        elif rod['resultado'][partida] == 'E':
            mandante = rod['time_mandante'][partida]
            visitante = rod['time_visitante'][partida]
            rm = rend(mandante,partida)
            rv = rend(visitante,partida)
            
            if rv <= 1/2:
                PC = dict_P[mandante]['PC']
                PC = (p*PC + (1-2*rv)*np.array([0,1/2,1/2])+2*rv*np.array([0,1,0]))/(p+1)
                dict_P[mandante]['PC'] = PC
                
            elif rv > 1/2:
                PC = dict_P[mandante]['PC']
                PC = (p*PC + (2*rv-1)*np.array([1/2,1/2,0])+2*(1-rv)*np.array([0,1,0]))/(p+1)
                dict_P[mandante]['PC'] = PC
                
            if rm <= 1/2:
                PF = dict_P[visitante]['PF']
                PF = (p*PF + (1-2*rm)*np.array([0,1/2,1/2])+2*rm*np.array([0,1,0]))/(p+1)
                dict_P[visitante]['PF'] = PF
            
            elif rm > 1/2:
                PF = dict_P[visitante]['PF']
                PF = (p*PF + (2*rm-1)*np.array([1/2,1/2,0])+2*(1-rm)*np.array([0,1,0]))/(p+1)
                dict_P[visitante]['PF'] = PF
        
        else:
            continue

prob_vectors()
##################################################
# Criando as simulações

## Parametros
dict_previsao = dict()

## Funcao para fazer as simulações
def simulacao(simulacao = 10000):

    ## Criando o Dataframe das rodadas restantes
    rod_rest = rod_total.copy()
    rod_rest = rod_rest.reset_index()
    rod_rest = rod_rest.drop(columns = ['index'])
    s=pd.Series(rod_rest['placar_mandante'].isna())
    for i in range(len(s)):
        if s[i]==False:
            rod_rest = rod_rest.drop(i)
    rod_rest = rod_rest.reset_index()
    rod_rest = rod_rest.drop(columns = ['index','placar_mandante','placar_visitante'])
    rod_rest.insert(2,'resultado','na')


    ## Criando a tabela que será utilizada na simulação
    df3 = df2.copy()
    df3.set_index('time',inplace = True)
    df3 = df3.drop(columns = ['gols_pro', 'gols_contra','saldo_gols','aproveitamento'])
    df_simu = df3.copy()


    ## Dicionário das probabilidades a ser atualizado nas simulações
    from copy import deepcopy
    dict_psimu = deepcopy(dict_P)


    ## Dicionário para contabilizar as vitórias
    dict_vit=dict()
    for time in times:
        dict_vit[time] = 0


    ## Fazendo a simulacao
    n=0
    while n < simulacao:
        
        # Rastreio da quantidade de simulações feitas
        if n % 10 == 0:
            print(n)
            import time
            print(time.time())
        
        # Simulando as partidas restantes
        for partida in range(len(rod_rest)):
            m = rod_rest['time_mandante'][partida]
            v = rod_rest['time_visitante'][partida]
            rm = dict_psimu[m]['r']
            rv = dict_psimu[v]['r']
            df_simu.loc[m]['jogos']+=1
            df_simu.loc[v]['jogos']+=1
            p=5
            
            # As chances do time mandante
            pvm = dict_psimu[m]['PC'][0]
            pem = dict_psimu[m]['PC'][1]
            pdm = dict_psimu[m]['PC'][2]
            
            # As chances do time visitante
            pvv = dict_psimu[v]['PF'][0]
            pev = dict_psimu[v]['PF'][1]
            pdv = dict_psimu[v]['PF'][2]
            
            # Vetor de probabilidade da partida
            pp = np.array([round((pvm+pdv)/2,3),round((pem+pev)/2,3),round((pdm+pvv)/2,3)])
            
            # Intervalos de probabilidade
            interv_m = np.arange(0,pp[0],0.001)
            interv_e = np.arange(pp[0],pp[0]+pp[1],0.001)
            interv_v = np.arange(pp[1]+pp[2],1,0.001)
            
            # Escolhendo aleatoriamente o resultado
            intervalo = np.arange(0,1,0.001)
            random.shuffle(intervalo)
            valor = round(intervalo[0],3)
            
            # Determinando o resultado
            
            if valor in interv_m: #vitoria do mandante
                PC = dict_psimu[m]['PC']
                PC = (p*PC + rv*np.array([1,0,0]))/(p + rv)
                dict_psimu[m]['PC'] = PC
            
                PF = dict_psimu[v]['PF']
                PF = (p*PF + (1-rm)*np.array([0,0,1]))/(p + (1 - rm))
                dict_psimu[v]['PF'] = PF
                
                df_simu.loc[m]['pontos']+=3
                dict_psimu[m]['r'] = df_simu.loc[m]['pontos']/df_simu.loc[m]['jogos']*3
                dict_psimu[v]['r'] = df_simu.loc[v]['pontos']/df_simu.loc[v]['jogos']*3
                
            elif valor in interv_v: #vitoria do visitante
                PF = dict_psimu[v]['PF']
                PF = (p*PF + rm*np.array([1,0,0]))/(p + rm)
                dict_psimu[v]['PF'] = PF
            
                PC = dict_psimu[m]['PC']
                PC = (p*PF + (1-rv)*np.array([0,0,1]))/(p + (1 - rv))
                dict_psimu[m]['PC'] = PC
                
                df_simu.loc[v]['pontos']+=3
                dict_psimu[m]['r'] = df_simu.loc[m]['pontos']/df_simu.loc[m]['jogos']*3
                dict_psimu[v]['r'] = df_simu.loc[v]['pontos']/df_simu.loc[v]['jogos']*3
                
            elif valor in interv_e: #empate
                if rv <= 1/2:
                    PC = dict_psimu[m]['PC']
                    PC = (p*PC + (1-2*rv)*np.array([0,1/2,1/2])+2*rv*np.array([0,1,0]))/(p+1)
                    dict_psimu[m]['PC'] = PC
                
                elif rv > 1/2:
                    PC = dict_psimu[m]['PC']
                    PC = (p*PC + (2*rv-1)*np.array([1/2,1/2,0])+2*(1-rv)*np.array([0,1,0]))/(p+1)
                    dict_psimu[m]['PC'] = PC
                
                if rm <= 1/2:
                    PF = dict_psimu[v]['PF']
                    PF = (p*PF + (1-2*rm)*np.array([0,1/2,1/2])+2*rm*np.array([0,1,0]))/(p+1)
                    dict_psimu[v]['PF'] = PF
            
                elif rm > 1/2:
                    PF = dict_psimu[v]['PF']
                    PF = (p*PF + (2*rm-1)*np.array([1/2,1/2,0])+2*(1-rm)*np.array([0,1,0]))/(p+1)
                    dict_psimu[v]['PF'] = PF
                
                df_simu.loc[m]['pontos']+=1
                df_simu.loc[v]['pontos']+=1
                dict_psimu[m]['r'] = df_simu.loc[m]['pontos']/df_simu.loc[m]['jogos']*3
                dict_psimu[v]['r'] = df_simu.loc[v]['pontos']/df_simu.loc[v]['jogos']*3
                

        # "Zerando" as variáveis
        # Salvando o resultado da última simulação        
        maior_pontuacao = df_simu['pontos'].max()
        df = df_simu.copy()
        df = df.reset_index()
        df.set_index('pontos',inplace=True)
        campeao = df.loc[maior_pontuacao,'time']
        dict_vit[campeao]+= 1
        n+=1
        dict_psimu = deepcopy(dict_P)
        df_simu = df3.copy()

    # Dicionário para retornar as chances de cada time no campeonato brasileiro                 
    for time in dict_vit:
        perc = str(round((dict_vit[time]/simulacao)*100,2))+"%"
        dict_previsao[time] = perc  

simulacao()

# Funcao que retorna as chances de um time no campeonato
def chances(time):
    try:
        return dict_previsao[time]  
    except NameError:
        print("Nome do time deve ser fornecido em formato de string")