﻿# -*- coding: utf-8 -*-
import sys
import urllib
import urllib2
import re
import json
from operator import itemgetter
from xml.dom import minidom

class OnDemand:
    _baseUrl = "http://www.rai.tv"
    _nothumb = "http://www.rai.tv/dl/RaiTV/2012/images/NoAnteprimaItem.png"

    editori = {"Rai1": "RaiUno", "Rai2": "RaiDue", "Rai3": "RaiTre",
               "Rai4": "Rai4", "Rai5": "Rai5", "Rai Gulp": "RaiGulp",
               "Rai Yoyo": "RaiYoYo", "Rai Movie": "RaiMovie",
               "Rai Fiction": "RaiFiction", "Rai Edu": "RaiEducational",
               "Rai Sport": "RaiSport", "Rai Internazionale": "RaiInternational",
               "Radio1": "Radio1", "Radio2": "Radio2", "Radio3": "Radio3",
               "Wr6": "WebRadio 6", "Wr7": "WebRadio 7", "Wr8": "WebRadio 8"}

    tematiche = ["Attualità", "Bianco e Nero", "Cinema", "Comici", "Cronaca", "Cucina", "Cultura", "Cultura e Spettacoli", "Economia", "Fiction",
        "Hi tech", "Inchieste", "Incontra", "Interviste", "Istituzioni", "Junior", "Moda", "Musica", "News", "Politica", "Promo", "Reality",
        "Salute", "Satira", "Scienza", "Società", "Spettacolo", "Sport", "Storia", "Telefilm", "Tempo libero", "Viaggi"]
    
    def getProgrammeList(self):
        url = "http://www.rai.tv/dl/RaiTV/programmi/ricerca/ContentSet-6445de64-d321-476c-a890-ae4ed32c729e-darivedere.html"
        response = json.load(urllib2.urlopen(url))
        return response

    def searchByIndex(self, index):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["index"] == index:
                programme["pageId"] = programme["linkDemand"][25:-5]
                result.append(programme)
        return result

    def searchByName(self, name):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["title"].lower().find(name) != -1:
                programme["pageId"] = programme["linkDemand"][25:-5]
                result.append(programme)
        return result

    def searchByChannel(self, channel):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if programme["editore"] == channel:
                programme["pageId"] = programme["linkDemand"][25:-5]
                result.append(programme)
        return result

    def searchByTheme(self, theme):
        programmes = self.getProgrammeList()
        result = []
        for programme in programmes:
            if theme in programme["tematiche"]:
                programme["pageId"] = programme["linkDemand"][25:-5]
                result.append(programme)
        return result

    def searchNewProgrammes(self):
        programmes = self.getProgrammeList()
        programmes = sorted(programmes, key = itemgetter("date"), reverse = True)[:10]
        result = []
        for programme in programmes:
                programme["pageId"] = programme["linkDemand"][25:-5]
                result.append(programme)
        return result

    def getProgrammeSets(self, pageId):
        url = "http://www.rai.tv/dl/RaiTV/programmi/%s.xml" % pageId
        xmldata = urllib2.urlopen(url).read()
        dom = minidom.parseString(xmldata)
        programmeSets = []
        for node in dom.getElementsByTagName('set'):
            name = node.attributes["name"].value
            uniquename = node.attributes["uniquename"].value
            try:
                types = node.getElementsByTagName('Summary')[0].getElementsByTagName('TypeOccurrency')
            except IndexError:
                types = []

            for typeoccurrency in types:
                # handle more than one media type
                mediatype = typeoccurrency.attributes["type"].value
                occurrency = typeoccurrency.attributes["occurrency"].value

                programmeSet = {}
                programmeSet["name"] = name
                programmeSet["count"] = occurrency
                programmeSet["uniquename"] =  uniquename
                    
                if mediatype == "RaiTv Media Video Item" and int(occurrency) > 0 :
                    programmeSet["mediatype"] = "V"
                    programmeSets.append(programmeSet)
                elif mediatype == "RaiTv Media Audio Item" and int(occurrency) > 0 :
                    programmeSet["mediatype"] = "A"
                    programmeSets.append(programmeSet)
                elif mediatype == "RaiTv Media Podcast Item" and int(occurrency) > 0 :
                    programmeSet["mediatype"] = "P"
                    programmeSets.append(programmeSet)
                elif mediatype == "RaiTv Media Foto Item":
                    pass
                    #programmeSet["mediatype"] = "F"
                    #programmeSets.append(programmeSet)

        return programmeSets

    def getItems(self, uniquename, count, mediatype):
        items = []
        i=0

        while len(items) < int(count):
            try:
                url = "http://www.rai.tv/dl/RaiTV/programmi/liste/%s-%s-%s.xml" % (uniquename, mediatype, i)
                xmldata = urllib2.urlopen(url).read()
            except urllib2.HTTPError, err:
                if err.code == 404:
                    # Premature EOF
                    break
                else:
                    raise

            dom = minidom.parseString(xmldata)
            i = i + 1
            
            for node in dom.getElementsByTagName('item'):
                item = {}
                item["name"] = node.attributes['name'].value
                units = node.getElementsByTagName('units')[0]
                try:
                    item["image"] = self._baseUrl + units.getElementsByTagName('imageUnit')[0].getElementsByTagName('image')[0].childNodes[0].data
                except IndexError:
                    item["image"] = self._nothumb
                try:
                    item["date"] = units.getElementsByTagName('dateUnit')[0].getElementsByTagName('date')[0].childNodes[0].data
                except IndexError:
                    item["date"] = node.attributes['createDate'].value
                
                if mediatype == "V":
                    item["url"] = units.getElementsByTagName('videoUnit')[0].getElementsByTagName('url')[0].childNodes[0].data
                    # if present then get h264 url
                    attributes = units.getElementsByTagName('videoUnit')[0].getElementsByTagName('attribute')
                    for attribute in attributes:
                        if attribute.getElementsByTagName('key')[0].childNodes[0].data == "h264":
                            item["url"] = attribute.getElementsByTagName('value')[0].childNodes[0].data
                elif mediatype == "A":
                    item["url"] = self._baseUrl + units.getElementsByTagName('audioUnit')[0].getElementsByTagName('url')[0].childNodes[0].data
                elif mediatype == "F":
                    # do not handle photos
                    pass
                elif mediatype == "P":
                    item["url"] = units.getElementsByTagName('linkUnit')[0].getElementsByTagName('link')[0].childNodes[0].data
                    
                items.append(item)

        return items


#ondemand = OnDemand()
#print ondemand.searchByIndex("b")
#print ondemand.searchByName("ball")
#print ondemand.searchByChannel("RaiFiction")
#print ondemand.searchByTheme("Fiction")
#print ondemand.searchByTheme("Società")
#print ondemand.searchNewProgrammes()
#print ondemand.getProgrammeSets("Page-5b3110f7-b13e-42e5-888d-c35e2119bf34")
#print ondemand.getItems("ContentSet-d77e7cf9-8688-4826-a9f3-736c9d1790b4", "29", "V")
#print ondemand.getItems("http://www.rai.tv/dl/RaiTV/programmi/liste/ContentSet-0c3cf090-9562-4de6-b204-39aca4848253-A-0.xml")
#print ondemand.getProgrammeSets("Page-f48c8dc0-351b-4765-96fa-38904b4ba863")
#print ondemand.getItems("http://www.rai.tv/dl/RaiTV/programmi/liste/ContentSet-4fe35ccb-6b29-4284-bad5-f9fa7a343b08-F-0.xml")
#print ondemand.getProgrammeSets("Page-a5ca5744-4390-41e9-925b-e9112705c830")
#print ondemand.getItems("http://www.rai.tv/dl/RaiTV/programmi/liste/ContentSet-c33f420f-62dc-4ed7-ba26-9684a1f97927-P-0.xml")
#print ondemand.getItems("http://www.rai.tv/dl/RaiTV/programmi/liste/ContentSet-13474b95-8e91-44e7-b1e0-9cb41387f1e9-V-0.xml")
#print ondemand.getProgrammeSets("Page-730a4f29-39e3-4796-83dd-236624e79c3f")
#print ondemand.getItems("http://www.rai.tv/dl/RaiTV/programmi/liste/ContentSet-4565a706-a94d-4387-9083-41a7e458c55c-V-0.xml")