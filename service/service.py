from PIL import Image, ImageFilter, ImageEnhance
from IPython.display import display
import pytesseract as tess
import os
from collections import Counter

def median_image_stack ( ims_rgb, stencil ) :
    from statistics import median
    
    def pattern ( pix, x, y ) :
        def indexed ( pix, x, y, idx ) :
            return pix[x,y][idx]
        r = []
        g = []
        b = []
        for dx in range(-stencil,stencil) :
            for dy in range(-stencil,stencil) :
                r.append( pix[x+dx,y+dy][0] )
                g.append( pix[x+dx,y+dy][1] )
                b.append( pix[x+dx,y+dy][2] )
        return [r, g, b]
    
    oversize = 5
    im_processed = Image.new("RGB", (ims[0].size[0] + oversize,ims[0].size[1] + oversize), (255, 255, 255))
    pix_processed = im_processed.load()
    
    for x in range(stencil,ims[0].size[0]-stencil) :
        for y in range(stencil,ims[0].size[1]-stencil) :
            
            rs = []
            gs = []
            bs = []
            white = False
            for im in ims_rgb :
                rgb = pattern(im.load(),x,y)
                rs.extend(rgb[0])
                gs.extend(rgb[1])
                bs.extend(rgb[2])                
                white |= im.load()[x,y] == (255,255,255)         
                
            if white :
                r = g = b = 255
            else :
                r = int(median(rs))
                g = int(median(gs))
                b = int(median(bs))
      
            pix_processed[x,y] = ( r, g, b )
    
    return im_processed
  
  def grey_filter_hsv( im, minsaturation, mindarkness ) :

    im_processed = Image.new("RGB", im.size, (255, 255, 255))
    pix_processed = im_processed.load()
    
    im_hsv = im.convert('HSV')
    pix_hsv = im_hsv.load()
    
    for x in range(1,im_processed.size[0]) :
        for y in range(1,im_processed.size[1]) :
         
            rgb = im.load()[x,y]
            r = rgb[0]
            g = rgb[1]
            b = rgb[2]
            
            saturation = pix_hsv[x,y][1]
            darkness = 255 - pix_hsv[x,y][2]

            # not enough saturation and not dark enough?
            if saturation < minsaturation & darkness < mindarkness :
                r = g = b = 255
                
            pix_processed[x,y] = ( r, g, b )
            
    return im_processed
  
  def unskew( img, shear=-0.3, crop=10 ) :
    return img.copy().transform(img.size, Image.AFFINE, (1, shear, 0, 0, 1, 0)).crop((crop,0,img.size[0],img.size[1]))
  
  def image_2_text( im ):
    
    def call_tesseract( im, psm ) :
        text = tess.image_to_string(im, config='--psm ' + str(psm)).strip() # , lang='eng'
        #print(text)
        return text
    
    recognized = []
    recognized.append(call_tesseract(im,6))
    recognized.append(call_tesseract(im,7))
    recognized.append(call_tesseract(im,8))
    recognized.append(call_tesseract(im,13))
    return Counter(recognized)
  
  def solve ( ims_rgb ) :
    recognized = Counter()

    for minsaturation in (30,50,70,90) :
        im_processed = median_image_stack( ims_rgb , 1 )
        #display(im_processed.resize((200,60), resample=Image.NEAREST))
        #display(im_processed)

        im_processed = grey_filter_hsv ( im_processed, minsaturation, 100 )
        #display(im_processed.resize((200,60), resample=Image.NEAREST))
        #display(im_processed)

        im_processed = unskew( im_processed )
        enhancer = ImageEnhance.Contrast(im_processed)
        im_processed = enhancer.enhance(1).filter(ImageFilter.BoxBlur(1))
        #display(im_processed)
        
        text = image_2_text( im_processed )
        recognized += text
        print(text)

    print("\nTotals: " + str(recognized))
    return recognized
  
from pydantic import BaseModel
from typing import List
from typing import Optional
from PIL import Image
import io
import base64

class Captcha(BaseModel):
    url: str
    imagedata: List[str]

@app.post("/captcha")
def solve_captcha(captcha: Captcha):
    #print(base64.b64decode(captcha.imagedata))
    images = []
    for s in captcha.imagedata :
        im = Image.open(io.BytesIO(base64.b64decode(s))).convert("RGB")
        images.append(im)
        #display(im)
    result = solve( images )
    return dict(result)
