import requests
import json
import logging
import pandas as pd
import glob
import os
import time
from retrying import retry, RetryError


"""
AZURE Face APIにデータを登録する
"""

SUBSCRIPTION_KEY  = "9b386e76643345bf9a3de504121a17f7"
GROUP_NAME = "kimono_search"
BASE_URL = "https://japaneast.api.cognitive.microsoft.com/face/v1.0/"
SRC_PATH = "/Users/taku/dev/Vasara/KimonoSearch/vasara_photo/photo/"
IMG_BASE_URL = "https://storage.googleapis.com/kimono_search/"

def main():

    """
    #Group削除処理
    ret = deleteGroup()

    #Group作成処理
    ret = makeGroup()

    #取り込み処理
    importPerson()

    """

    #学習処理
    trainGroup()

    #内容チェック
    checkPerson()
  


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

#画像グループの作成
def makeGroup():
    end_point = BASE_URL + "persongroups/" + GROUP_NAME
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
    print (r.text)

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def makePerson(name,userData):
    end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/persons"
    print (end_point)
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
    print (r.text)
    personId = r.json()["personId"]
    return personId

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def addFaceToPerson(personId, imageURL):
    if personId != None:
        print(personId)
        end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/persons/" + personId  + "/persistedFaces"
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
            print("Successfuly added face to person")
            print (r.text)
            persistedFaceId = r.json()
        except Exception as e:
            print("Failed to add a face to person")
            print(e)
            persistedFaceId = None
        return persistedFaceId
    else:
        print("personId is not set.")

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def deletePerson(personId):
    print ("deletePerson: " + personId)
    if personId != None:
        print(personId)
        end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/persons/" + personId
        print(end_point)
        headers = {
            "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
        }
        r = requests.delete(
            end_point,
            headers = headers
        )
      
        try:
            print("Successfuly delete person")
            print (r.text)
            persistedFaceId = r.json()
        except Exception as e:
            print("Failed to delete person")
            print(e)
            persistedFaceId = None

    else:
        print("personId is not set.")


@retry(stop_max_attempt_number=10,wait_fixed=5000)
def trainGroup():
    print("trainGroup")
    end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/train"
    print(end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.post(
        end_point,
        headers = headers,
    )
    print(r.text)

@retry(stop_max_attempt_number=10,wait_fixed=5000)
def detectFace(imageUrl):
    end_point = BASE_URL + "detect"
    print (end_point)
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
        print("faceId Found:{}".format(faceId))
        return r.json()[0]
    except Exception as e:
        print("faceId not found:{}".format(e))
        return None
   
@retry(stop_max_attempt_number=10,wait_fixed=5000)
def identifyPerson(faceId):
    end_point = BASE_URL + "identify"
    print (end_point)
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
    print(r.text)
    return r.json()[0]


@retry(stop_max_attempt_number=10,wait_fixed=5000)
def getPersonInfoByPersonId(personId):
    end_point = BASE_URL + "persongroups/" + GROUP_NAME + "/persons/" + personId
    print (end_point)
    headers = {
        "Ocp-Apim-Subscription-Key" :SUBSCRIPTION_KEY
    }
    r = requests.get(
        end_point,
        headers = headers
    )
    print(r.text)
    return r.json()


@retry(stop_max_attempt_number=10,wait_fixed=5000)
def deleteGroup():
    end_point = BASE_URL + "persongroups/" + GROUP_NAME
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
    print (r.text)


#テスト用ロジック
def checkPerson():
   #画像から、personを特定するときのサンプルコードです。
    image = "https://cdn.mainichi.jp/vol1/2016/09/02/20160902ddm001010041000p/9.jpg?1"
    faceId = detectFace(image)
    person = identifyPerson(faceId["faceId"])
    if person["candidates"]: #学習データに候補があれば
        personId = person["candidates"][0]["personId"]
        confidence = person["candidates"][0]["confidence"]
        personInfo = getPersonInfoByPersonId(personId)
        print("name=" + personInfo["name"])
        print("data=" + personInfo["userData"])
        print("confidence=" + str(confidence))

    else:
        print ("No candidates found")
    


if __name__ == '__main__':
    main()

