#!/usr/bin/env python

"""
複数人写ってる着物写真から、一人を残してマスクをする
"""


import cv2
import dlib
import numpy

import os
import os.path
import sys
import shutil
import logging

import config

logging.basicConfig(filename='logging.log',level=logging.DEBUG)

PREDICTOR_PATH = config.PREDICTOR_PATH
SRCPATH = config.SRCPATH
DESTPATH = config.DESTPATH


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

img_extensions = [".jpg",".JPG",".jpeg",".JPEG"]

SCALE_FACTOR = 1

class OneFace(Exception):
    pass

class NoFaces(Exception):
    pass

def main():

    #対象フォルダリストよりファイルを取得
    #SRCPATH配下のフォルダリストを取得
    for dir in [f for f in os.listdir(SRCPATH) if os.path.isdir(os.path.join(SRCPATH, f))]:
        
        #DESTPATHにフォルダがなければ、作成
        src_path = SRCPATH + "/" + dir
        dest_path = DESTPATH + "/" + dir
        if not (os.path.isdir(dest_path)):
            os.mkdir(dest_path)
            logging.info("make dir: " + dest_path)

        #フォルダ内のファイルを取得
        files = os.listdir(src_path)
        for  file_name in [f for f in files if os.path.isfile(os.path.join(src_path, f))]:

            #既にある処理済みのファイルはスキップ
            name, ext = os.path.splitext(file_name)
            if(os.path.isfile(DESTPATH + "/" + file_name) or os.path.isfile(DESTPATH + "/" + file_name + "_1")):
                logging.info(name + " is skip")
                continue

            #拡張子で画像のみを対象に
            name, ext = os.path.splitext(file_name)
            if(ext in img_extensions):
                logging.info(src_path + "/" + file_name)

                #処理用画像作成処理
                mask_face_and_write(src_path + "/" + file_name, dest_path)
        


def mask_face_and_write(fname,dest_path):
    logging.info("make_face_and_write: " + fname)

    try:
        im, landmarks = read_im_and_landmarks(fname)
    except OneFace:
        #一人だけの場合は、そのままファイルをコピー
        logging.info(fname + " One Face")
        basename = os.path.basename(fname)

        dst = DESTPATH + "/" + basename
        shutil.copyfile(fname,dst)
        return

    except NoFaces:
        logging.info(fname + " No Faces")
        return

    #複数人の顔を、一人を除いて塗りつぶし
    for cnt,j in enumerate(landmarks):
        im1 = im.copy()
        basename = os.path.basename(fname)
        name, ext = os.path.splitext(basename)
        dstfilename = dest_path + "/" + name + '_' + str(cnt) + ext
 
        #複数人の顔を、一人を除いて塗りつぶし
        for i,rect in enumerate(landmarks):
            if(cnt != i):
                cv2.rectangle(im1, (rect.left(),rect.top()),(rect.right(),rect.bottom()), (0, 255, 0),thickness=-1)
        
        cv2.imwrite(dstfilename, im1)

        logging.info("write: " +  dstfilename)


def get_landmarks(im):
    landmark = []
    rects = detector(im, 1)

    if len(rects) == 0:
        raise NoFaces
    if len(rects) == 1:
        raise OneFace

    #for rect in rects:
    #    landmark.append(numpy.matrix([[p.x, p.y] for p in predictor(im, rect).parts()]))
    
    #return landmark
    return rects

def read_im_and_landmarks(fname):
    im = cv2.imread(fname, cv2.IMREAD_COLOR)
    im = cv2.resize(im, (im.shape[1] * SCALE_FACTOR,
                         im.shape[0] * SCALE_FACTOR))
    s = get_landmarks(im)

    return im, s


if __name__ == "__main__":
    main()
