import requests
import json
import logging
import pandas as pd
import glob
import os
import time
import sys
import traceback
from retrying import retry, RetryError

import config

"""
AZURE Face APIにデータを登録する
"""

SUBSCRIPTION_KEY  = config.SUBSCRIPTION_KEY
GROUP_NAME = config.GROUP_NAME
BASE_URL = config.BASE_URL
IMG_SRC_PATH = config.IMG_SRC_PATH
IMG_BASE_URL = config.IMG_BASE_URL

logging.basicConfig(filename='logging.log',level=logging.DEBUG)


#
#argument
# make:     make group
# delete:   delete group
# import:   import image data
# train:    train data

def main(argv):

    if argv[1] == "make":
        #Group作成処理
        makeGroup()

    elif argv[1] == "delete":
        #Group削除処理
        deleteGroup()

    elif argv[1] == "import":
        #取り込み処理
        importPerson()

    elif argv[1] == "train":
        #学習処理
        trainGroup()
  
    else:
        print("argument")
        print(" make:     make group")
        print(" delete:   delete group")
        print(" import:   import image data")
        print(" train:    train data")


#画像グループの作成
def makeGroup():
    logging.info("makeGroup:")
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME
    payload = {
        "name": GROUP_NAME
    }
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.put(
        end_point,
        headers = headers,
        json = payload
    )
    logging.info(r.text)

#画像グループ削除
def deleteGroup():
    logging.info("deleteGroup:")
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME
    payload = {
        "name": GROUP_NAME
    }
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.delete(
        end_point,
        headers = headers,
        json = payload
    )
    logging.info(r.text)


def importPerson():
    #取り込み処理
    #IMG_SRCPATHフォルダ内の画像を学習させる
    #IMG_SRCPATH配下のフォルダリストを取得
    for dir in [f for f in os.listdir(IMG_SRC_PATH) if os.path.isdir(os.path.join(IMG_SRC_PATH, f))]:
        logging.info("input dir: " + dir)

        #dir配下のファイルを学習
        files = glob.glob(IMG_SRC_PATH + "/" + dir + "/*")
        for file in files:
            logging.info("input file: " + file)
            name = os.path.basename(file)

            image = IMG_BASE_URL + dir + "/" + name 
            link = IMG_BASE_URL + dir + "/" + name
            #personを登録し、personIdを返す
            personId = makePerson(name,link)
            #personIdをもとに、そのpersonに画像を追加する
            persistedFaceId = addFaceToPerson(personId, image)
      
            #persistedFaceIdが取得できない時は、personIdを削除する
            if persistedFaceId == None:
                deletePerson(personId)


#personを登録し、personIdを返す
@retry(stop_max_attempt_number=10,wait_fixed=5000)
def makePerson(name,userData):
    logging.info("makePerson: " + name)
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons"
    logging.info(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    payload = {
        "name": name,
        "userData": userData
    }
    r = requests.post(
        end_point,
        headers = headers,
        json = payload
    )
    logging.info(r.text)
    personId = r.json()["personId"]
    return personId

#personIdをもとに、そのpersonに画像を追加する
@retry(stop_max_attempt_number=10,wait_fixed=5000)
def addFaceToPerson(personId, imageURL):
    logging.info("addFaceToPerson: " + imageURL)
    if personId != None:
        logging.info("addFaceToPerson personId: " + personId)
        end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons/" + personId  + "/persistedFaces"
        logging.info("addFaceToPerson end_point: " + end_point)
        logging.info("addFaceToPerson imageURL: " + imageURL)
        headers = {
            "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
        }
        payload = {
            "url": imageURL
        }
        r = requests.post(
            end_point,
            headers = headers,
            json = payload
        )
      
        try:
            logging.info("Successfuly added face to person")
            logging.info(r.text)
            persistedFaceId = r.json()
        except Exception as e:
            logging.info("Failed to add a face to person")
            logging.info(traceback.format_exc())
            persistedFaceId = None
        return persistedFaceId
    else:
        logging.info("personId is not set.")

#personIdを削除する
@retry(stop_max_attempt_number=10,wait_fixed=5000)
def deletePerson(personId):
    logging.info("deletePerson: " + personId)
    if personId != None:
        logging.info(personId)
        end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons/" + personId
        logging.info("endPoint: " + end_point)
        headers = {
            "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
        }
        r = requests.delete(
            end_point,
            headers = headers
        )
      
        try:
            logging.info("Successfuly delete person")
            logging.info(r.text)
            persistedFaceId = r.json()
        except Exception as e:
            logging.info("Failed to delete person")
            logging.info(traceback.format_exc())
            persistedFaceId = None

    else:
        logging.info("personId is not set.")


#学習処理
def trainGroup():
    logging.info("trainGroup")
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/train"
    logging.info(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.post(
        end_point,
        headers = headers,
    )
    logging.info(r.text)


if __name__ == '__main__':
    main(sys.argv)

