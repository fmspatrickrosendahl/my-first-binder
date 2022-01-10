import pickle
import numpy as np

from multiprocessing import Process
from wait4it import wait_for

from pydantic import BaseModel
from typing import List
from typing import Optional
from PIL import Image

import io
import base64

import os
from PIL import Image

import uvicorn
from fastapi import FastAPI

class CaptchaSolver:
    rects = []
    kmeans1 = None
    groups1 = None
    kmeans2 = None
    groups2 = None
    kmeans3 = None
    groups3 = None
    kmeans4 = None
    groups4 = None
    def predict( self, im ):
        display(im)
        def predictdigit( di, kmeans, groups ) :
            display(di)
            return groups[kmeans.predict( [np.array(di.convert("L").getdata()) ] )[0]]
        result =  predictdigit( im.copy().crop(self.rects[0]), self.kmeans1, self.groups1 )
        result += predictdigit( im.copy().crop(self.rects[1]), self.kmeans2, self.groups2 )
        result += predictdigit( im.copy().crop(self.rects[2]), self.kmeans3, self.groups3 )
        result += predictdigit( im.copy().crop(self.rects[3]), self.kmeans4, self.groups4 )
        return result

solver = pickle.load( open( "sitc1_solver.p", "rb" ) )

app = FastAPI()

class Captcha(BaseModel):
    url: str
    imagedata: str

@app.post("/captcha")
def solve_captcha(captcha: Captcha):
    #print(base64.b64decode(captcha.imagedata))
    im = Image.open(io.BytesIO(base64.b64decode(captcha.imagedata))).convert("RGB")
    display(im)
    result = {'result' : solver.predict( im )}
    print(result)
    return dict(result)
