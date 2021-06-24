import os
from os import path
from dotenv import load_dotenv

import tweepy
import re
import csv
import datetime as dt

import cardapiogetter as cg

load_dotenv()

# Authenticate to Twitter
auth = tweepy.OAuthHandler(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'])
auth.set_access_token(os.environ['TOKEN'], os.environ['TOKEN_SECRET'])

# Create API object
api = tweepy.API(auth)

#dicionário para "traduzir" os dias da semana de modo que o código possa achar a header correta
diasSemana ={
    "Saturday": "Sábado",
    "Sunday": "Domingo",
    "Monday": "Segunda-Feira",
    "Tuesday": "Terça-Feira",
    "Wednesday": "Quarta-Feira",
    "Thursday": "Quinta-Feira",
    "Friday": "Sexta-Feira"
}

#dicionário para lidar com as variáveis de campus
campus = {
    "IFCSPV":{
        "url": "https://docs.google.com/spreadsheets/d/1gymUpZ2m-AbDgH7Ee7uftbqWmKBVYxoToj28E8c-Dzc/pubhtml",
        "nome": "IFCS/PV",
        "nomeArq": "IFCS-PV"
    },
    "fundao": {
        "url": "https://docs.google.com/spreadsheets/d/1YvCqBrNw5l4EFNplmpRBFrFJpjl4EALlVNDk3pwp_dQ/pubhtml",
        "nome": "Fundão",
        "nomeArq": "Fundao"
    }
}

#dicionário para substituir a descrição dos pratos por emojis
wordToEmoji = {
    "Entrada": "🥗",
    "Prato Principal": "🍲",
    "Prato Vegetariano": "🥦",
    "Guarnição": "🥘",
    "Acompanhamentos": "🍛",
    "Acompanhamento": "🍛",
    "Sobremesa": "🍬",
    "Sobremesa ": "🍬",
    "Refresco": "🥤"
}

#pegar o dia da semana atual e traduzi-lo
weekDay = dt.datetime.now().strftime("%A")
diaDaSemana = diasSemana[weekDay]

#pegar o mês atual
month = dt.datetime.now().strftime("%m")
completeDay = dt.datetime.now().strftime("%d-%m-%Y")

#pegar o ano
year = dt.datetime.now().strftime("%Y")

#abreviar o dia da semana caso seja "___-feira"
if diaDaSemana != "Sábado" and diaDaSemana != "Domingo":
    diaDaSemanaText = diaDaSemana[:-6]
else:
    diaDaSemanaText = diaDaSemana

#função para pegar e transformar em string de tweet o cardapio completo de almoço e jantar de um campus específico
def getCardapioCampus(keyCampus):
    
    campusName = campus[keyCampus]['nome']
    campusArqName = campus[keyCampus]['nomeArq']

    #chama a função getLunchDinner do módulo cardapiogetter passando a url do cardápio do campus como parâmetro e designa
    #a variável 'lunch' ao primeiro item da lista que a função retorna e a variável 'dinner' ao segundo item
    lunchAndDinner = cg.getCardapio(campus[keyCampus]["url"])
    lunchArray = lunchAndDinner[0]
    dinnerArray = lunchAndDinner[1]

    #chama as funções getLunchSpecific e getDinnerSpecific, que pegam os dataframes lunchArray e dinnerArray e o nome
    #campus para gerar o tweet que será postado.
    string_lunch = getLunchSpecific(lunchArray, campusName)
    string_dinner = getDinnerSpecific(dinnerArray, campusName)

    #guarda o cardápio da semana em um csv separado caso seja segunda-feira.
    if diaDaSemana == "Segunda-Feira":
        if not path.exists(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv"):
            cardapiomes = open(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv", 'w')
            cardapio_writer = csv.writer(cardapiomes, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            cardapio_writer.writerow(["nome_prato", "tipo_prato", "dia_semana", "dia_mes", "turno", "campus"])
        with open(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv", 'a') as cardapiomes:
            cardapio_writer = csv.writer(cardapiomes, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            cardapio_writer.writerow(["nome_prato", "tipo_prato", "dia_semana", "dia_mes", "turno"])

            for index, row in lunchArray.iterrows():
                tipoPrato = row['ALMOÇO']
                for column in lunchArray:
                    if column != 'ALMOÇO':
                        cardapio_writer.writerow([row[column], tipoPrato, column, completeDay, "Almoço"])

            for index, row in dinnerArray.iterrows():
                tipoPrato = row['JANTAR']
                for column in dinnerArray:
                    if column != 'JANTAR':
                        cardapio_writer.writerow([row[column], tipoPrato, column, completeDay, "Jantar"])

    return [string_lunch, string_dinner]

#função para pegar o almoço de um campus específico
def getLunchSpecific(lunch, campusNome):

    #compõe o início da string de almoço, parte do texto que será postado como tweet. Inclue o nome do campus, valor encontrado
    #como um dos valores da keyCampus no dicionário campus.
    tweet_string_lunch = f"({diaDaSemanaText}) Almoço em "+ campusNome + ":\n"

    #designa o almoço do dia, procurando os resultados da coluna 'ALMOÇO' (que possui informação de tipo de prato) e da coluna
    #do dia da semana correspondente, que possui o nome do prato a ser servido. Adiciona os resultados a uma lista.
    dayLunch = lunch[['ALMOÇO', diaDaSemana]]
    dayLunchPlates = dayLunch.values.tolist()

    #itera por cada prato da lista dayLunchPlates, que é uma outra lista composta por tipo de prato e nome do prato, e adiciona
    #as informações à string de almoço, com uma quebra de linha no final de cada prato. Muda o tipo de prato para um emoji,
    #para economizar caracteres.
    for plate in dayLunchPlates:
        tweet_string_lunch += wordToEmoji[plate[0]]+" -> "+plate[1]+"\n"

    #confere se a string final é maior que 220 caracteres. Se for, tenta abreviar o nome do dia da semana para apenas três letras
    if len(tweet_string_lunch)>=220:
        print("String too big. Reajusting...")
        oldName = re.search(r'\(([^)]+)', tweet_string_lunch).group(1)
        newName = oldName[:3]
        tweet_string_lunch = tweet_string_lunch.replace(oldName, newName)


    #retorna a string já composta pelo cardápio do almoço
    return tweet_string_lunch

#função para pegar o jantar de um campus específico
def getDinnerSpecific(dinner, campusNome):

    #compõe o início da string de jantar, parte do texto que será postado como tweet. Inclue o nome do campus, valor encontrado
    #como um dos valores da keyCampus no dicionário campus.
    tweet_string_dinner = f"({diaDaSemanaText}) Jantar em "+ campusNome + ":\n"

    #designa o jantar do dia, procurando os resultados da coluna 'ALMOÇO' (que possui informação de tipo de prato) e da coluna
    #do dia da semana correspondente, que possui o nome do prato a ser servido. Adiciona os resultados a uma lista.
    dayDinner = dinner[['JANTAR', diaDaSemana]]
    dayDinnerPlates = dayDinner.values.tolist()

    #itera por cada prato da lista dayDinnerPlates, que é ainda outra lista composta por tipo de prato e nome do prato,
    #e adiciona as informações à string de jantar, com uma quebra de linha no final de cada prato. Muda o tipo de prato
    #para um emoji, para economizar caracteres.
    for plate in dayDinnerPlates:
        tweet_string_dinner +=  wordToEmoji[plate[0]]+" -> "+plate[1]+"\n"

    #confere se a string final é maior que 220 caracteres. Se for, tenta abreviar o nome do dia da semana para apenas três letras
    if len(tweet_string_dinner)>=220:
        print("String too big. Reajusting...")
        oldName = re.search(r'\(([^)]+)', tweet_string_dinner).group(1)
        newName = oldName[:3]
        tweet_string_dinner = tweet_string_dinner.replace(oldName, newName)

    #retorna a string já composta pelo cardápio do jantar
    return tweet_string_dinner

strings_ifcspv = getCardapioCampus("IFCSPV")
strings_fundao = getCardapioCampus("fundao")

#função que divide o tweet em dois, com as duas últimas linhas em um segundo tweet
def splitTweet(tweet):
    tweet1 = "\n".join(tweet.split("\n")[0:-3])
    tweet2 = tweet.split("\n",6)[6]
    return [tweet1, tweet2]

#função que posta os tweets. Ela confere se cada tweet da array possui menos de 220 caracteres.
#Se o tweet ultrapassar os 220 caracteres a função chama a função splitTweet
#e posta os tweets divididos, com o segundo como resposta do primeiro.
def postTweets(stringArray):
    for string in stringArray:
        if len(string) >= 220:
            newTweets = splitTweet(string)
            firstTweet = api.update_status(newTweets[0])
            api.update_status('@bandejaobotufrj'+newTweets[1], firstTweet.id_str)
        else:
            api.update_status(string)

#chama a função postTweets para as arrays de tweets dos dois campus
postTweets(strings_ifcspv)
postTweets(strings_fundao)
