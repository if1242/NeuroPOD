# -*- coding: utf-8 -*-
import conf
import telebot
import socket
import socks

from PIL import Image, ExifTags
from scipy.misc import imresize
import numpy as np
from keras.models import load_model
import tensorflow as tf

ip = '85.25.207.105'
port =  61116 
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, ip, port)
socket.socket = socks.socksocket

bot = telebot.TeleBot(conf.token)

model = load_model('./model/main_model.hdf5', compile=False)
graph = tf.get_default_graph()

def ml_predict(image):
    with graph.as_default():
        prediction = model.predict(image[None, :, :, :])
    prediction = prediction.reshape((224,224, -1))
    return prediction
    

def rotate_by_exif(image):
    try :
        for orientation in ExifTags.TAGS.keys() :
            if ExifTags.TAGS[orientation]=='Orientation' : break
        exif=dict(image._getexif().items())
        if not orientation in exif:
            return image

        if   exif[orientation] == 3 :
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6 :
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8 :
            image=image.rotate(90, expand=True)
        return image
    except:
        return image

THRESHOLD = 0.5    
@bot.message_handler(content_types=["text"])
def repeat_all_messages(message): 
    bot.send_message(message.chat.id, "Загрузите фото для обработки!")
    
@bot.message_handler(content_types=['photo'])
def photo(message):
    file_id = message.photo[2].file_id
    newFile = bot.get_file(file_id)
    downloaded_file = bot.download_file(newFile.file_path)
    with open('new_file.jpg', 'wb') as new_file:
         new_file.write(downloaded_file)
    f = open('1.png', 'r')
    read_data = f.read()
    
    image = Image.open('new_file.jpg')
    image = rotate_by_exif(image)
    resized_image = imresize(image, (224, 224)) / 255.0
    prediction = ml_predict(resized_image[:, :, 0:3])
    prediction = imresize(prediction[:, :, 1], (image.height, image.width))
    prediction[prediction>THRESHOLD*255] = 255
    prediction[prediction<THRESHOLD*255] = 0
    transparent_image = np.append(np.array(image)[:, :, 0:3], prediction[: , :, None], axis=-1)
    transparent_image = Image.fromarray(transparent_image)
    width = 132
    ratio = (width / float(transparent_image.size[0]))
    height = int(float(transparent_image.size[1]) * float(ratio))
    transparent_image = transparent_image.resize((width, height)) 
    res_img = Image.new("RGB", (396, 360), (255, 255, 255))
    res_img.paste(transparent_image, (0, 0), transparent_image)
    res_img.paste(transparent_image, (132, 0), transparent_image)
    res_img.paste(transparent_image, (264, 0), transparent_image)
    res_img.paste(transparent_image, (0, 170), transparent_image)
    res_img.paste(transparent_image, (132, 170), transparent_image)
    res_img.paste(transparent_image, (264, 170), transparent_image)
    with open('res_file.png', 'wb') as image_file:
        res_img.save(image_file, 'PNG')
        image_file.close()

    bot.send_photo(message.chat.id, photo=open('res_file.png', 'r')) 

if __name__ == '__main__':
     bot.polling(none_stop=True)
