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

PREDICTOR_PATH = "/Users/taku/dev/Vasara/KimonoSearch/vasara_photo/shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)

SRCPATH = "/Users/taku/Google Drive File Stream/マイドライブ/着物写真(店舗撮影用)/"
img_extensions = [".jpg",".JPG",".jpeg",".JPEG"]

SCALE_FACTOR = 1

DESTPATH = "/Users/taku/dev/Vasara/KimonoSearch/vasara_photo/photo/"

TARGETPATH = ["鎌倉駅前店","秋葉原 神田明神店","鎌倉小町通り店","浅草寺店"]

class OneFace(Exception):
    pass

class NoFaces(Exception):
    pass

def main():
    # fname = os.path.basename(sys.argv[1])

    #対象フォルダリストよりファイルを取得
    #for dir in [f for f in os.listdir(SRCPATH) if os.path.isdir(os.path.join(SRCPATH, f))]:
    #残りのパスに対して処理
    for dir in TARGETPATH:

        src_path = SRCPATH + dir
        files = os.listdir(src_path)

        #フォルダ内のファイルを取得
        for  file_name in [f for f in files if os.path.isfile(os.path.join(src_path, f))]:

            #既にある処理済みのファイルはスキップ
            name, ext = os.path.splitext(file_name)
            if(os.path.isfile(DESTPATH + file_name) or os.path.isfile(DESTPATH + file_name + "_1")):
                print(name + " is skip")
                continue

            #拡張子で画像のみを対象に
            name, ext = os.path.splitext(file_name)
            if(ext in img_extensions):
                print(src_path + "/" + file_name)

                #処理用画像作成処理
                mask_face_and_write(src_path + "/" + file_name)


def mask_face_and_write(fname):

    try:
        im, landmarks = read_im_and_landmarks(fname)
    except OneFace:
        #一人だけの場合は、そのままファイルをコピー
        print(fname + " One Face")
        basename = os.path.basename(fname)

        dst = DESTPATH + basename
        shutil.copyfile(fname,dst)
        return

    except NoFaces:
        print(fname + " No Faces")
        return

    #複数人の顔を、一人を除いて塗りつぶし
    for cnt,j in enumerate(landmarks):
        im1 = im.copy()
        basename = os.path.basename(fname)
        name, ext = os.path.splitext(basename)
        dstfilename = DESTPATH + name + '_' + str(cnt) + ext
 
        #複数人の顔を、一人を除いて塗りつぶし
        for i,rect in enumerate(landmarks):
            if(cnt != i):
                cv2.rectangle(im1, (rect.left(),rect.top()),(rect.right(),rect.bottom()), (0, 255, 0),thickness=-1)
        
        cv2.imwrite(dstfilename, im1)

        print("write: " +  dstfilename)


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
