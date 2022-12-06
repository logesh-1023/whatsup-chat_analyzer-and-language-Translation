#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import re
import pdfkit  
from cgitb import text
import email
from gettext import translation
from importlib.resources import path
from string import octdigits
from tokenize import String
from turtle import Screen
import numpy
from email import header
from fileinput import close
from http import server
import io
import itertools
from operator import concat, index
import sys
import csv
from typing import Text, final
import emoji
from collections import Counter
from flask import Flask,render_template,request
app=Flask(__name__,template_folder='template')
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/submit",methods=['GET', 'POST'])
def submit():
  if request.method=='POST':
    analyze=[] #->RETURN OUTPUT
    nameoffile=request.form['myFile']
    list4=[]
    lini=[]
    # imported from current directory
    from chatline import Chatline
    from font_color import Color
    """
    CLI Set
    """
    parser = argparse.ArgumentParser(
        description='Read and analyze whatsapp chat',
        usage="python whatsapp_analyzer.py"
    )

    stop_words_options = [ "arabic","bulgarian","catalan","czech","danish","dutch","english","finnish","french","german","hebrew","hindi","hungarian","indonesian","italian","malaysian","norwegian","polish","portuguese","romanian","russian","slovak","spanish","swedish","turkish","ukrainian","vietnamese"]

    parser.add_argument(
        '-s', 
        '--stopword', 
        required=False, 
        choices=stop_words_options,  
        metavar='',
        help="Stop Words: A stop word is a commonly used word (such as 'the', 'a', 'an', 'in').\
            In order to get insightful most common word mentioned in the chat, we need to skip these type of word.\
            The Allowed values are: " + ", ".join(stop_words_options))

    parser.add_argument(
        '-c', 
        '--customstopword', 
        required=False, 
        metavar='',
        help="Custom Stop Words. File path to stop word. File must a raw text. One word for every line"
    )

    args = parser.parse_args()

    """
    READ FILE
    """
    try:
        with io.open(r"E:\WhatsApp-Analyzer-master\WhatsApp-Analyzer-master\%s"%nameoffile, "r", encoding="utf-8") as file:
            lines = file.readlines()
        
    except IOError as e:
        print("File \"" + args.file + "\" not found. Please recheck your file location")
        sys.exit()

    stop_words = []
    if args.stopword:
        try:
            with io.open("stop-words/" + args.stopword + ".txt", "r", encoding="utf-8") as file:
                stop_words = [x.strip() for x in file.readlines()]
        except IOError as e:
            print("Stop Words file not found in \"" + args.file + "\" not found.")
            sys.exit()


    if args.customstopword:
        try:
            with io.open(args.customstopword, "r", encoding="utf-8") as file:
                stop_words = [x.strip() for x in file.readlines()]
        except IOError as e:
            print("Stop Words file not found in \"" + args.file + "\" not found.")
            sys.exit()
            
    """
    PARSING AND COUNTING
    """
    chat_counter = {
        'chat_count': 0,
        'deleted_chat_count': 0,
        'event_count': 0,
        'senders': [],
        'timestamps': [],
        'words': [],
        'domains': [],
        'emojis': [],
        'fav_emoji': [],
        'fav_word': []
    }


    previous_line = None
    for line in lines:
        chatline = Chatline(line=line, previous_line=previous_line)
        previous_line = chatline
        lini.append(line)
        # Counter
        if chatline.line_type == 'Chat':
            chat_counter['chat_count'] += 1

        if chatline.line_type == 'Event':
            chat_counter['event_count'] += 1

        if chatline.is_deleted_chat:
            chat_counter['deleted_chat_count'] += 1

        if chatline.sender is not None:
            chat_counter['senders'].append(chatline.sender)
            for i in chatline.emojis:
                chat_counter['fav_emoji'].append((chatline.sender, i))
            
            for i in chatline.words:
                chat_counter['fav_word'].append((chatline.sender, i))

        if chatline.timestamp:
            chat_counter['timestamps'].append(chatline.timestamp)

        if len(chatline.words) > 0:
            chat_counter['words'].extend(chatline.words)

        if len(chatline.emojis) > 0:
            chat_counter['emojis'].extend(chatline.emojis)

        if len(chatline.domains) > 0:
            chat_counter['domains'].extend(chatline.domains)

    for i in chat_counter["timestamps"]:
        list4.append(i)


    """
    REDUCE AND ORDER DATA
    """

    def reduce_and_sort(data):
        return sorted(
            dict(
                zip(
                    Counter(data).keys(), 
                    Counter(data).values()
                )
            ).items(), 
            key=lambda x: x[1],
            reverse=True
        )

    def reduce_and_filter_words(list_of_words):
        val = [w.lower() for w in list_of_words if (len(w) > 1) and (w.isalnum()) and (not w.isnumeric()) and (w.lower() not in stop_words)]
        return val

    def filter_single_word(w):
        return (len(w) > 1) and (w.isalnum()) and (not w.isnumeric()) and (w.lower() not in stop_words)

    def reduce_fav_item(data):
        exist = []
        arr = []
        for i in data:
            if i[1] > 0 and not i[0][0] in exist:
                exist.append(i[0][0])
                arr.append(i)
        return arr
        
    chat_counter['senders'] = reduce_and_sort(chat_counter['senders'])
    chat_counter['words'] = reduce_and_sort(reduce_and_filter_words(chat_counter['words']))
    chat_counter['domains'] = reduce_and_sort(chat_counter['domains'])
    chat_counter['emojis'] = reduce_and_sort(chat_counter['emojis'])
    chat_counter['timestamps'] = reduce_and_sort([(x.strftime('%A'), x.strftime('%H')) for x in chat_counter['timestamps']])
    chat_counter['fav_emoji'] = reduce_fav_item(reduce_and_sort(chat_counter['fav_emoji']))
    chat_counter['fav_word'] = reduce_fav_item(reduce_and_sort([x for x in chat_counter['fav_word'] if filter_single_word(x[1])]))
    """
    VISUALIZE
    """
    def printBar (value, total, label = '', prefix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        filledLength = int(value / (total / length))
        bar = fill * filledLength + '' * (length - filledLength)
        print("\r{} |{} {}".format(label, bar, Color.bold(str(value))), end = printEnd)
        print()

    def printBarChart(data, fill="█"):
        if len(data) <= 0:
            print("Empty data")
            return
        
        total = max([x[1] for x in data])
        max_label_length = len(sorted(data, key=lambda tup: len(tup[0]), reverse=True)[0][0])
        for i in data:
            label = i[0] + " " * (max_label_length - len(i[0]))
            printBar(i[1], total, length=50, fill=fill, label=label)

    def printCalendar(data):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hours = ['0' + str(x) if len(str(x)) < 2 else str(x) for x in range(24)]
        max_val = float(data[max(data, key=data.get)]) if len(data) else 0

        ticks = [
            0,
            0.25 * max_val,
            0.50 * max_val,
            0.75 * max_val,
        ]

        sys.stdout.write("     ")
        for day in days:
            sys.stdout.write('\t[' + day[:3] + "]")
            
        sys.stdout.write('\n')

        for hour in hours:
            sys.stdout.write("[" + hour + ':00]')
            
            for day in days:
                
                dict_key = (day, hour)
                
                if dict_key in data:
                    # tick = str(ct[dict_key])
                    
                    if data[dict_key] > ticks[3]:
                        tick = Color.custom("███", bold=True, fg_red=True)
                    elif data[dict_key] > ticks[2]:
                        tick = Color.custom("▓▓▓", bold=True, fg_orange=True)
                    elif data[dict_key] > ticks[1]:
                        tick = Color.custom("▒▒▒", bold=True, fg_green=True)
                    else:
                        tick = Color.custom("░░░", bold=True, fg_light_grey=True)
                else:
                    tick = Color.custom('===', bold=False, fg_white=True)
                
                sys.stdout.write('\t ' + tick)
            sys.stdout.write('\n')
            
    # Senders
    data = chat_counter['senders']
    analyze.append(Color.red("-" * 50))
    analyze.append(Color.red("Chat Count by Sender"))
    analyze.append(Color.red("-" * 50))
    a4=("Active Sender : "+ Color.red("{}".format(len(data))))
    a5=("Total Chat : "+ Color.red("{}".format(sum([x[1] for x in data]))))
    a6=("Average : "+Color.red("{:.1f} chat per member".format((sum([x[1] for x in data]) / len(data)) if len(data) else 0)))
    print()
    a7=(data[:20])
    if len(data) > 20:
        analyze.append("---")
        analyze.append("Other from {} member | {}".format(Color.red(str(len(data[20:]))), Color.red(str(sum([x[1] for x in data[20:]])))))
    print()
    print()

    # Domains
    data = chat_counter['domains']
    a8=(Color.blue("-" * 50))
    a9=(Color.blue("Mentioned Domain (Shared Link/URL)"))
    a10=(Color.blue("-" * 50))
    a11=("Domain Count : "+ Color.blue(str(len(data))))
    a12=("Mention Count : "+ Color.blue(str(sum([x[1] for x in data]))))
    print()
    a13=(data[:20])
    if len(data) > 20:
        analyze.append("---")
        analyze.append("Other {} domain | {}".format(Color.blue(str(len(data[20:]))), Color.blue(str(sum([x[1] for x in data[20:]])))))
    print()


    # Emojis
    data = [(x[0] + " (" + emoji.demojize(x[0]) + ") ", x[1]) for x in chat_counter['emojis']]
    a13=(Color.orange("-" * 50))
    a14=(Color.orange("Used Emoji"))
    a15=(Color.orange("-" * 50))
    a16=("Unique Emoji : "+ Color.orange(str(len(data))))
    a17=("Total Count : "+ Color.orange(str(sum([x[1] for x in data]))))
    print()
    a18=(data[:20])
    if len(data) > 20:
        analyze.append("---")
        analyze.append("Other {} emoji | {}".format(Color.orange(str(len(data[20:]))), Color.orange(str(sum([x[1] for x in data[20:]])))))
    print()
    print()

    # Fav Emojis
    data = [(x[0][0] + " Favorite Emoji " + x[0][1] +" Times Used : " + str(x[1])) for x in chat_counter['fav_emoji']]
    a19=(Color.orange("-" * 50))
    a20=(Color.orange("Favorite Emoji by Member"))
    a21=(Color.orange("-" * 50))
    print()
    a22=(data[:20])
    print()
    print()

    # Words
    data = chat_counter['words']
    a23=(Color.green("-" * 50))
    a24=(Color.green("Used Word"))
    a25=(Color.green("-" * 50))
    a26=("Unique Word : "+ Color.green(str(len(data))))
    a27=("Total Count : "+ Color.green(str(sum([x[1] for x in data]))))
    print()
    a28=(data[:20])
    if len(data) > 20:
        analyze.append("---")
        analyze.append("Other {} word | {}".format(Color.green(str(len(data[20:]))), Color.green(str(sum([x[1] for x in data[20:]])))))
    print()
    print()

    # Fav Word
    data = [(x[0][0] + " Favorite Word : " + x[0][1] + " No of Times Used : " +str(x[1])) for x in chat_counter['fav_word']]
    a29=(Color.green("-" * 50))
    a30=(Color.green("Favorite Word by Member"))
    a31=(Color.green("-" * 50))
    print()
    a32=(data[:20])
    print()

    # Heatmap
    data = chat_counter['timestamps']
    a33=(Color.purple("-" * 50))
    a34=(Color.purple("Chat Activity Heatmap"))
    a35=(Color.purple("-" * 50))
    a41=""
    a42=""
    if len(data) > 0:
        a41=("Most Busy : {}, at {} ({} chat)".format(
            Color.purple(str(data[0][0][0])), 
            Color.purple(str(data[0][0][1]) + ":00"), 
            Color.purple(str(data[0][1]))))
        a42=("Most Silence : {}, at {} ({} chat)".format(
            Color.purple(str(data[-1][0][0])), 
            Color.purple(str(data[-1][0][1]) + ":00"), 
            Color.purple(str(data[-1][1]))))
    print()
    a37=('---')
    a38=('X: DAY')
    a39=('Y: DATE')
    a40=('---')
    a43=('Less [{}{}{}{}{}] More'.format(
        Color.custom("===", bold=False), 
        Color.custom("░░░", bold=True, fg_light_grey=True),
        Color.custom("▒▒▒", bold=True, fg_green=True),
        Color.custom("▓▓▓", bold=True, fg_orange=True),
        Color.custom("███", bold=True, fg_red=True)
    ))
    analyze=[a4,a5,a6,a7,a8,a9,a10,a11,a12,a13,a14,a15,a16,a17,a18,a19,a20,a21,a22,a23,a24,a25,a26,a27,a28,a29,a30,a31,a32,a33,a34,a41,a42,a35,a37,a38,a39,a40]
    dummyarr=[]
    for i in analyze:
        lines= re.sub("[()'\[\]]","",str(i))
        dummyarr.append(lines)
    
    #BADWORD
    Name=chat_counter['senders'][0]
    list1=[]
    list2=[]
    msg=""
    TEXT=""
    c=0
    for x in chat_counter['words']:
            list1.append(x[0])
    file=open('bad-words.csv')
    type(file)
    csvreader=csv.reader(file)
    header=[]
    header=next(csvreader)
    for row in csvreader:
        list2.append(row[0])
    list5=[]
    list6=[]
    list3=[]
    for i in chat_counter['words']:
        for j in list2:
            if i[0]==j:
                list5.append(j)
    for k in list5:
        h=1
        for o in lini:
            char=o.split()
            for r in char:
                if k==r:
                    list6.append(h)
            h=h+1
    c=1
    for i in list4:
        for j in list6:
            if c==j:
             list3.append(i)
        c=c+1

    for (i,j) in itertools.zip_longest(list5,list3):
        TEXT=TEXT+"ABUSIVE WORD RECEIVED:"+i+"  "+" TIME :"+str(j)+"\n" 

    TEXT="This is the Person abused me : "+Name[0]+"\n"+TEXT
    #Mailer
    qemail=request.form['email']
    import smtplib
    server=smtplib.SMTP_SSL("smtp.gmail.com",465)
    server.login("logeshfire6@gmail.com","jatxquxctpxcqklg")
    SUBJECT="ABUSED ALERT!"
    mg='Subject:{}\n\n{}'.format(SUBJECT, TEXT)
    server.sendmail("logeshfire6@gmail.com","{}".format(qemail),mg)
    server.quit()

    return render_template("analysis.html",name=dummyarr)
  else:
    return "Exception"
#translation
@app.route("/result",methods=['GET', 'POST'])
def result():
  if request.method=='POST':
    imgname=request.form['image']
    destlan=request.form['Language']
    from PIL import Image
    from pytesseract import pytesseract
    path_to_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    path_to_image =(r'E:\WhatsApp-Analyzer-master\WhatsApp-Analyzer-master\source\%s'%(imgname))
    pytesseract.tesseract_cmd = path_to_tesseract
    img = Image.open(path_to_image)
    text = pytesseract.image_to_string(img)
    text=text.replace("!","")
    text=text.replace(".","")
    text=text.replace("'","")
    wordz=re.split("\n",text)
    # dummy=""
    # for i in wordz:
    #     dummy=dummy+i+" "

    #englishp=[]
    single=[]
    # file=open('4000-most-common-english-words-csv.csv')
    # type(file)
    # csvreader=csv.reader(file)
    # header=[]
    # header=next(csvreader)
    # for row in csvreader:
    #     englishp.append(row[0])
    # wordz1=dummy.split(" ")
    # for i in wordz:
    #     if i!=" ":
    #      #for j in englishp:
    #         #if i==j:
    #         single.append(i)
    output=[]
    language=[]
    #englishtoTamil
    from googletrans import Translator,constants
    #source
    translator=Translator()
    iot=[]
    # text5=""
    # text5=single[0]
    # detection = translator.detect(text5)
    # dect=detection.lang
    #languages
    language.append(constants.LANGUAGES)
    #translation
    for i in wordz:
        eachLine = re.split(" ",i)
        concatLine=""
        for j in eachLine:
            translations=translator.translate(j,dest=destlan)
            concatLine = concatLine+str(f"{translations.text}")+" "
        single.append(concatLine)      
    # for translation in translations:   # type: ignore
    #  output.append(f"{translation.text}")
    # print(output)
    # for i in output:
    #     iot.append(i)
    # config = pdfkit.configuration(wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")  
    # #  N0]+Cn?> ./""<Ṁ /'|
    # pdfkit.from_file('analysis.html','out.pdf')
    return render_template("analysis.html",name=single)
  else:
    return "exception"
@app.route("/contact.html")
def contact():
    return render_template("contact.html")
@app.route("/about.html")
def about():
    return render_template("about.html")
@app.route("/index.html")
def index():
    return render_template("index.html")
@app.route("/services.html")
def service():
    return render_template("services.html")
if __name__=='__main__':
 app.run(debug=True,port=5001)