import os
from os import path
from dotenv import load_dotenv

import tweepy
import re
import csv
import datetime as dt
from pytz import timezone

import cardapiogetter as cg

load_dotenv()

# Configurar fuso horário
tz = timezone('America/Sao_Paulo')

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
    "Guarnição 1": "🥘",
    "Guarnição 2": "🥘",
    "Acompanhamentos": "🍛",
    "Acompanhamento": "🍛",
    "Sobremesa": "🍬",
    "Sobremesa ": "🍬",
    "Refresco": "🥤"
}

# pegar data atual
date = dt.datetime.now(tz=tz)
print(date)

#pegar o dia da semana atual e traduzi-lo
weekDay = date.strftime("%A")
diaDaSemana = diasSemana[weekDay]
print(weekDay, diaDaSemana)

#pegar o mês atual
month = date.strftime("%m")
completeDay = date

#pegar o ano
year = date.strftime("%Y")

#abreviar o dia da semana caso seja "___-feira"
if diaDaSemana != "Sábado" and diaDaSemana != "Domingo":
    diaDaSemanaText = diaDaSemana[:-6]
else:
    diaDaSemanaText = diaDaSemana


# recebe o DataFrame com cardápio de almoço de um campus específico e devolve o(s) tweet(s) montados para postar
def createLunchTweet(lunch, campusNome):

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
        try:
            if(plate[0] != "Atenção o cardápio poderá sofrer alteração sem comunicação prévia"):
                tweet_string_lunch += wordToEmoji[plate[0]]+" -> "+plate[1]+"\n"
        except KeyError as e:
            print("Erro na chave:", e)

    #confere se a string final é maior que 220 caracteres. Se for, tenta abreviar o nome do dia da semana para apenas três letras
    if len(tweet_string_lunch)>=220:
        print("String too big. Reajusting...")
        oldName = re.search(r'\(([^)]+)', tweet_string_lunch).group(1)
        newName = oldName[:3]
        tweet_string_lunch = tweet_string_lunch.replace(oldName, newName)


    #retorna a string já composta pelo cardápio do almoço
    return tweet_string_lunch


# recebe o DataFrame com cardápio de jantar de um campus específico e devolve o(s) tweet(s) montados para postar
def createDinnerTweet(dinner, campusNome):

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
        try:
            if(plate[0] != "Atenção o cardápio poderá sofrer alteração sem comunicação prévia"):
                tweet_string_dinner += wordToEmoji[plate[0]]+" -> "+plate[1]+"\n"
        except KeyError as e:
            print("Erro na chave:", e)

    #confere se a string final é maior que 220 caracteres. Se for, tenta abreviar o nome do dia da semana para apenas três letras
    if len(tweet_string_dinner)>=220:
        print("String too big. Reajusting...")
        oldName = re.search(r'\(([^)]+)', tweet_string_dinner).group(1)
        newName = oldName[:3]
        tweet_string_dinner = tweet_string_dinner.replace(oldName, newName)
    #confere se a string tem algum espaço extra. Se tiver, normaliza para apenas um espaço
    tweet_string_dinner = re.sub(r'([ ]{2,})', ' ', tweet_string_dinner)
    #retorna a string já composta pelo cardápio do jantar
    return tweet_string_dinner

# chama as funções de formatação dos tweets de almoço e jantar para um campus específico.
# Também guarda o cardápio desse campus em um CSV toda segunda feira
def getCardapioCampus(keyCampus):

    campusName = campus[keyCampus]['nome']
    campusArqName = campus[keyCampus]['nomeArq']

    # cg.getCardapio acessa a url em que o cardápio está postado e devolve os dados em uma array de DataFrames:
    # um para almoço e um para jantar
    lunchAndDinner = cg.getCardapio(campus[keyCampus]["url"])
    lunchDF = lunchAndDinner[0]
    dinnerDF = lunchAndDinner[1]

    # retornam os tweets que serão postados
    string_lunch = createLunchTweet(lunchDF, campusName)
    string_dinner = createDinnerTweet(dinnerDF, campusName)


    #guarda o cardápio da semana em um csv separado caso seja segunda-feira.
    if diaDaSemana == "Segunda-Feira":
        try:
            if not path.exists(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv"):

                cardapiomes = open(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv", 'w', encoding='utf-8')
                cardapio_writer = csv.writer(cardapiomes, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                cardapio_writer.writerow(["nome_prato", "tipo_prato", "dia_semana", "dia_mes", "turno", "campus"])

            with open(f"./data/cardapiomes{month}-{year}-{campusArqName}.csv", 'a', encoding='utf-8') as cardapiomes:

                cardapio_writer = csv.writer(cardapiomes, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                for index, row in lunchDF.iterrows():
                    i = 0
                    tipoPrato = row['ALMOÇO']
                    for column in lunchDF:
                        if column != 'ALMOÇO':
                            columnCompleteDate = completeDay+dt.timedelta(days=i)
                            columnDate = columnCompleteDate.strftime("%d-%m-%Y")
                            cardapio_writer.writerow([row[column], tipoPrato, column, columnDate, "Almoço", campusArqName])
                            i+=1

                for index, row in dinnerDF.iterrows():
                    j = 0
                    tipoPrato = row['JANTAR']
                    for column in dinnerDF:
                        if column != 'JANTAR':
                            columnCompleteDate = completeDay+dt.timedelta(days=j)
                            columnDate = columnCompleteDate.strftime("%d-%m-%Y")
                            cardapio_writer.writerow([row[column], tipoPrato, column, columnDate, "Jantar", campusArqName])
                            j+=1
        except Exception as e:
            print(e)

    print("tweets criados")
    return [string_lunch, string_dinner]


strings_ifcspv = getCardapioCampus("IFCSPV")
strings_fundao = getCardapioCampus("fundao")

#utilitário que divide o tweet em dois, com as duas últimas linhas em um segundo tweet
def splitTweet(tweet):
    tweet1 = "\n".join(tweet.split("\n")[0:-3])
    tweet2 = tweet.split("\n",6)[6]
    return [tweet1, tweet2]

#função que posta os tweets. Ela confere se cada tweet da array possui menos de 220 caracteres.
#Se o tweet ultrapassar os 220 caracteres, chama a função splitTweet
# e posta os tweets divididos com o segundo como resposta do primeiro.
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