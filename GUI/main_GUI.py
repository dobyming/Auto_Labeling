from msilib.schema import Font
from tkinter import *
import tkinter.font as tkfont
from tkinter import filedialog
from turtle import width
import scrapy
from scrapy.crawler import CrawlerProcess 
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from urllib.parse import quote_plus
from urllib.request import urlopen
import urllib.request
import sys
import time
import os
import boto3
from requests import session
import cv2
import numpy as np
import shutil

main = Tk()
main.title('Image Auto Labeling Tool')
main.geometry('620x500')
main.resizable(False, False)

def classification(path_dir, search):
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    print(net.getUnconnectedOutLayers())
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    # Loading image
    #path_dir = 'C://Users//Joon//Auto_Labeling//auto_labeling//car'
    #search = 'car'
    file_list = os.listdir(path_dir)
    os.mkdir(path_dir + "//noclass")

    for imgfile in file_list:
        # img_name = "test.jpg"
        img = cv2.imread(path_dir + "/" + imgfile)
        img_name = imgfile
        #img = cv2.resize(img, None, fx=0.5, fy=0.5)
        height, width, channels = img.shape

        # Detecting objects
        blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

        net.setInput(blob)
        outs = net.forward(output_layers)

        # Showing informations on the screen
        class_ids = []
        confidences = []
        boxes = []
        detections = []
        labels = []
        count = 0
        sum_confidence = 0

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    sum_confidence += confidence
                    count += 1
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    detections.append([detection[0],detection[1],detection[2],detection[3]])
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
                    labels.append(str(classes[class_id]))

        #print(labels)
        file_destination = path_dir + "//noclass"
        if not search in labels:
            shutil.move(path_dir + "//" + imgfile, file_destination)


#크롤링 창  
def createCrawlpage():
    Crawlpage = Toplevel(main)
    Crawlpage.geometry('700x300') 
    Crawlpage.resizable(False, False)
    Crawlpage.title("Image Crawling")

    ctitlesize = tkfont.Font(size=20)
    cpsize = tkfont.Font(size=11)
    crawl_label1 = Label(Crawlpage,text="크롤링", height="3",font=ctitlesize)   
    crawl_label2 = Label(Crawlpage,text="크롤링할 이미지를 검색하세요. ", height="3",font=cpsize)   
    
    search = StringVar() #검색어변수 = search 
    ctextbox = Entry(Crawlpage,width=20,textvariable=search) #검색어 입력부 
    ctextbox.place(x=270, y=150)
   
    #구글 크롤링
    def Gtest():
        #Chrome(spider #1)
        class GcrawlerSpider(scrapy.Spider):
            #Base_URL Setting
            name = 'gcrawler'
            allowed_domains = ['www.google.com']
            start_urls = ['http://www.google.com']

            keyword = search.get()
            if(keyword=='end'):
                sys.exit(0)

            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get("https://www.google.co.kr/imghp?hl=ko&ogbl")
            elem = driver.find_element_by_name("q") #google 검색어 입력 부분
            elem.send_keys(keyword) #keyboard입력값을 전송할 수 있음
            elem.send_keys(Keys.RETURN) #enter키를 입력 받음


            #scroll을 끝까지 내려서 모든 사진을 다 다운받을 수 있게끔함
            SCROLL_PAUSE_TIME = 2
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height: 
                    try:
                        driver.find_element_by_css_selector(".mye4qd").click()
                    except:
                        break
                last_height = new_height

            #디렉토리 생성
            def create_folder(directory):
                try:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                except OSError:
                    print("Error : Creating Directory. "+directory)
            
            save_path = './img/'+keyword+"/"
            crawl_file = create_folder(save_path)
            dir_path = './img/'+keyword

            #이미지를 긁어오기(Crawling)
            images= driver.find_elements_by_css_selector(".rg_i.Q4LuWd")
            cnt=1
            for image in images:
                try:
                    image.click()
                    imgUrl = driver.find_element_by_css_selector(".n3VNCb").get_attribute("src")
                    with urllib.request.urlopen(imgUrl) as f:
                        with open(save_path + keyword + str(cnt) + '.jpg', 'wb') as h:
                            img = f.read()
                            h.write(img)
                    cnt+=1
                except:
                    pass   
            classification(dir_path, keyword)
            driver.close()

    #네이버 크롤링 
    def Ntest():
        #Naver(spider #2)
        class ImgcrawlerSpider(scrapy.Spider):
            #Base_URL Setting
            name = 'imgcrawler'
            allowed_domains = ['www.naver.com']
            base = 'https://search.naver.com/search.naver?where=image&section=image&query='

            keyword = search.get()
            if(keyword=='end'):
                sys.exit(0)
                
            search_url = base+quote_plus(keyword)
            driver = webdriver.Chrome(ChromeDriverManager().install())
            driver.get(search_url)
            
            #scroll_down 구현부(body)
            SCROLL_PAUSE_TIME = 2
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height: 
                    break
                last_height = new_height

            #디렉토리 생성
            def create_folder(directory):
                try:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                except OSError:
                    print("Error : Creating Directory. "+directory) 
            save_path = './img/'+keyword+"/"
            crawl_file = create_folder(save_path)
            dir_path = './img/'+keyword

            #이미지를 긁어오기(Crawling)
            images = driver.find_elements_by_class_name("_image")
            cnt=1
            for image in images:
                try:
                    imgUrl= image.get_attribute('src')
                    with urllib.request.urlopen(imgUrl) as f:
                        with open(save_path + keyword + str(cnt) + '.jpg', 'wb') as h:
                            img = f.read()
                            h.write(img)
                    cnt+=1
                except:
                    pass    
            classification(dir_path, keyword)
            driver.close()
  

    Gsearch_btn = Button(Crawlpage,text="구글",command=Gtest) #구글 검색 버튼
    Gsearch_btn.place(x=230, y=193)
    Nsearch_btn = Button(Crawlpage,text="네이버",command=Ntest) #네이버 검색 버튼
    Nsearch_btn.place(x=286, y=193)
    Pexel_btn = Button(Crawlpage,text="Pexel",command="") #Pexel 검색 버튼(미완성)
    Pexel_btn.place(x=350, y=193)
    Pixaby_btn = Button(Crawlpage,text="Pixaby",command="") #Pixaby 검색 버튼(미완성)
    Pixaby_btn.place(x=410, y=193)

    #폴더열기
    folder_btn = Button(Crawlpage,text="폴더열기",command=folder_open)
    folder_btn.place(x=312, y=253)

    crawl_label1.pack() 
    crawl_label2.pack()

def folder_open():
    filedialog.askopenfilename(initialdir='./img',title='파일선택', filetypes=(('jpg files','*.jpg'),('all files','*.*')))

def createAutolabeling():
    dirPath = filedialog.askdirectory(parent=main, initialdir="/", title='폴더를 선택해주세요.')

    # Load Yolo
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    print(net.getUnconnectedOutLayers())
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))

    # Loading image
    path_dir = dirPath
    file_list = os.listdir(path_dir)

    for imgfile in file_list:
        # img_name = "test.jpg"
        img = cv2.imread(path_dir + "/" + imgfile)
        img_name = imgfile
        #img = cv2.resize(img, None, fx=0.5, fy=0.5)
        height, width, channels = img.shape

        # Detecting objects
        blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)

        net.setInput(blob)
        outs = net.forward(output_layers)

        # Showing informations on the screen
        class_ids = []
        confidences = []
        boxes = []
        detections = []
        count = 0
        sum_confidence = 0
        precision = 0

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    sum_confidence += confidence
                    count += 1
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    
                    detections.append([detection[0],detection[1],detection[2],detection[3]])
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        # precision = sum_confidence/count
        # print(imgfile + "  정확도: " + str(round(precision, 4)*100))
        
        if count == 0 or sum_confidence/count < 0.7:
            os.mkdir(path_dir + "/" + "inspection")
            shutil.move(path_dir + "//" + imgfile, path_dir + "//inspection")
        else:
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            font = cv2.FONT_HERSHEY_PLAIN
            out_file = open(path_dir + "/" + img_name.rsplit(".")[0] + ".txt", 'w', encoding='utf-8')
            for i in range(len(boxes)):
                if i in indexes:
                    x, y, w, h = boxes[i]
                    d1,d2,d3,d4 = detections[i]
                    out_file.write("%d %.6f %.6f %.6f %.6f\n" % (class_ids[i], d1, d2, d3, d4))
                    # print(detections[i])
                    # print(class_ids[i])
                    label = str(classes[class_ids[i]])
                    color = colors[class_ids[i]]
                    cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(img, label, (x, y + 30), font, 3, color, 3)

#데이터셋 공유 창
def createSharepage():
    Sharepage = Toplevel(main)
    dirpath = Entry(Sharepage,width=100) #파일경로 불러옴 
    dirpath.pack(fill="x",padx=1,pady=1)

    #파일 경로를 불러옴
    def file_find():
        Sharepage.dirName=filedialog.askdirectory()
        dirpath.delete(0,END)
        dirpath.insert(END,Sharepage.dirName + "/")

    #AWS 권한 명시 
    session=boto3.Session(
        aws_access_key_id='AKIAXZWL4PM4KT75FEOG',
        aws_secret_access_key='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',
        region_name='ap-northeast-2'
        )
    s3 = session.client('s3')

    #업로드 할 s3 버킷명
    bucket='autolabeling'

    #폴더 업로드
    def upload_dir():
        local_dir=dirpath.get()
        # enumerate local files recursively
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                # construct the full local path
                local_path = os.path.join(root, filename)
                
                # construct the full Dropbox path
                relative_path = os.path.relpath(local_path, local_dir)

                #parsing 1 (경로의 마지막에 /가 포함된 경우 이를 삭제)
                if local_dir=="":
                    pass
                elif local_dir[-1]=="/":
                    local_dir=local_dir[:-1:]
                #parsing 2 (크롤링한 객체에 대해서만 dir명을 return)
                new_path = os.path.basename(local_dir)
                s3_path = os.path.join(new_path+"/", relative_path) #실제 s3에 업로드되는 경로를 생성 
            
                print ('Searching "%s" in "%s"' % (s3_path, bucket))
                try:
                    s3.head_object(Bucket=bucket, Key=s3_path)
                    print ("Path found on S3! Skipping %s..." % s3_path)
                except:
                    print ("Uploading %s..." % s3_path)
                    s3.upload_file(local_path, bucket, s3_path)

    #다운로드 페이지(다운로드 할 클래스를 사용자가 직접 입력후, 그 검색어에 따라 폴더가 로컬컴에 저장됌)
    def download_page():
        dpage = Tk()
        dpage.title('Download Class')
        dpage.geometry('500x200')
        dpage.resizable(False, False)

        dsize = tkfont.Font(size=10)
        D_label = Label(dpage,text="다운로드 할 클래스를 입력하세요.",height="3",font=dsize)
        D_label.pack()

        class_search = StringVar()
        dtextbox = Entry(dpage,width=20,textvariable=class_search)
        dtextbox.place(x=180,y=90)

        def downloadDirectoryFroms3(): #사용자의 입력을 통해 Class별 폴더를 다운로드 받음 
            s3_resource = boto3.resource('s3')
            bucket = s3_resource.Bucket('autolabeling')
            downvar = dtextbox.get()
            for obj in bucket.objects.filter(Prefix= downvar+"/"): 
                if not os.path.exists(os.path.dirname(obj.key)):
                    os.makedirs(os.path.dirname(obj.key))
                bucket.download_file(obj.key,obj.key)            
    
        download_btn = Button(dpage,text="다운로드",command=downloadDirectoryFroms3) 
        download_btn.place(x=220,y=130)


    fr_bt = Frame(Sharepage)
    fr_bt.pack(fill="x",padx=1,pady=1)

    bt_find = Button(fr_bt,text="Download",width=10, command=download_page) #command로는 download page로 이동함
    bt_find.pack(side="right",padx=1,pady=1)
    bt_upload = Button(fr_bt,text="Upload",width=10,command=upload_dir) #업로드 버튼
    bt_upload.pack(side="right",padx=1,pady=1)
    bt_find = Button(fr_bt,text="Find",width=10,command=file_find) #dir 불러오는 버튼
    bt_find.pack(side="right",padx=1,pady=1)

    Sharepage.title("Dataset Share") #창 title


#초기화면 제목부 
fontsize = tkfont.Font(size=20)
title_label = Label(main,text="Image Auto Labeling Tool", height="3",font=fontsize)

#초기화면 버튼부 
crawl_btn = Button(main, text="크롤링", width="17", height="5",command=createCrawlpage)
crawl_btn.place(x=80, y=200)
label_btn = Button(main, text="자동라벨링", width="17", height="5", command=createAutolabeling)
label_btn.place(x=260, y=200)
share_btn=Button(main,text="데이터셋 공유",width="17",height="5",command=createSharepage)
share_btn.place(x=450,y=200)

title_label.pack()
main.mainloop() 