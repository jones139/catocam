#!/usr/bin/env python

import cv2

def scaleW(img, newWidthPx=640):
    ''' Scale image img to have a new width newWidthPx pixels, retaining the 
        image aspect ratio.
        Returns a new opencv image.
    '''
    h, w, c = img.shape
    #print("initial w,h=%d,%d" % (w,h))
    wNew = newWidthPx
    hNew = int(h*wNew/w)
    #print("new w,h=%d,%d" % (wNew, hNew))
    imgScaled = cv2.resize(img, (wNew, hNew))
    return(imgScaled)
