import requests
import json
import logging
import pandas as pd
import glob
import os
import time
import sys
from retrying import retry, RetryError

import config

"""
AZURE Face APIにデータを登録する
"""

SUBSCRIPTION_KEY  = config.SUBSCRIPTION_KEY
GROUP_NAME = config.GROUP_NAME
BASE_URL = config.BASE_URL
SRC_PATH = config.IMG_SRC_PATH
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
    logger.info("makeGroup:")
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
    logger.info(r.text)

#画像グループ削除
def deleteGroup():
    logger.info("deleteGroup:")
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
    logger.info(r.text)


def importPerson():
    #取り込み処理
    #SRCPATHフォルダ内の画像を学習させる
    files = glob.glob(SRC_PATH + "/*")
    for file in files:
        name = os.path.basename(file)

        image = IMG_BASE_URL + name
        link = IMG_BASE_URL + name
        #personを登録し、personIdを返す
        personId = makePerson(name,link)
        #personIdをもとに、そのpersonに画像を追加する
        persistedFaceId = addFaceToPerson(personId, image)
      
        #persistedFaceIdが取得できない時は、personIdを削除する
        if persistedFaceId == None:
            deletePerson(personId)


@retry(stop_max_attempt_number=10,wait_fixed=5000)
def makePerson(name,userData):
    logger.info("makePerson: " + name)
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons"
    logger.info(end_point)
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
    logger.info(r.text)
    personId = r.json()["personId"]
    return personId

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def addFaceToPerson(personId, imageURL):
    logger.info("addFaceToPerson: "imageURL)
    if personId != None:
        print(personId)
        end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons/" + personId  + "/persistedFaces"
        print(end_point)
        print(imageURL)
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
            logger.info("Successfuly added face to person")
            logger.info(r.text)
            persistedFaceId = r.json()
        except Exception as e:
            logger.info("Failed to add a face to person")
            logger.info(traceback.format_exc())
            persistedFaceId = None
        return persistedFaceId
    else:
        logger.info("personId is not set.")

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def deletePerson(personId):
    logger.info("deletePerson: " + personId)
    if personId != None:
        logger.info(personId)
        end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons/" + personId
        logger.info("endPoint: " + end_point)
        headers = {
            "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
        }
        r = requests.delete(
            end_point,
            headers = headers
        )
      
        try:
            logger.info("Successfuly delete person")
            logger.info(r.text)
            persistedFaceId = r.json()
        except Exception as e:
            logger.info("Failed to delete person")
            logger.info(traceback.format_exc())
            persistedFaceId = None

    else:
        logger.info("personId is not set.")


#学習処理
def trainGroup():
    logger.info("trainGroup")
    end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/train"
    logger.info(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.post(
        end_point,
        headers = headers,
    )
    logger.info(r.text)

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def detectFace(imageUrl):
    end_point = BASE_URL + "detect"
    logger.info(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    payload = {
        "url": imageUrl
    }
    r = requests.post(
        end_point,
        json = payload,
        headers = headers
    )
    try:
        faceId = r.json()[0]["faceId"]
        logger.info("faceId Found:{}".format(faceId))
        return r.json()[0]
    except Exception as e:
        logger.info("faceId not found:{}".format(e))
        return None
   
@retry(stop_max_attempt_number=10,wait_fixed=5000)
def identifyPerson(faceId):
    end_point = BASE_URL + "identify"
    logger.info(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    faceIds = [faceId]
    payload = {
       "faceIds" :faceIds,
       "personGroupId" :GROUP_NAME,
    }
    r = requests.post(
        end_point,
        json = payload,
        headers = headers
    )
    logger.info(r.text)
    return r.json()[0]


def getPersonInfoByPersonId(personId):
    end_point = BASE_URL + "largepersongroups/" + GROUP_NAME + "/persons/" + personId
    print (end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.get(
        end_point,
        headers = headers
    )
    logger.info(r.text)
    return r.json()

if __name__ == '__main__':
    main(sys.argv)

