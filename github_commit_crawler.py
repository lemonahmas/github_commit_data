#-*- coding: UTF-8 -*-
import itertools
import json
import os,time,re,csv
import scrapy
from scrapy import Request
from datetime import datetime
import requests


class GithubSpider(scrapy.spiders.Spider):

    name = "github" #爬虫名称
    allowed_domains = ["github.com"] #制定爬取域名
    num = 1 # 页数，默认从第一页开始
    handle_httpstatus_list = [404, 403, 401] #如果返回这个列表中的状态码，爬虫也不会终止
    output_file = open('PR.txt', "w")
    output_csv = open("PR.csv","w",newline="")
    csv_writer = csv.writer(output_csv)    
    

    #token列表
    token_list = [
        
    ]
    token_iter = itertools.cycle(token_list) #生成循环迭代器，迭代到最后一个token后，会重新开始迭代


    def __init__(self): #初始化
        scrapy.spiders.Spider.__init__(self)
        self.csv_writer.writerow(["number","owner","title","created_at","updated_at","closed_at",\
                                  "issue_url","diff_url","PR_lived","events_url","labels","issue_created_at",\
                                "issue_closed_at","lines_changed"])

    def __del__(self): #爬虫结束时，关闭文件
        self.output_file.close()
        self.output_csv.close()

    def start_requests(self):
        start_urls = [] #初始爬取链接列表
        #url = "https://api.github.com/repos/golang/go/issues?q=is%3Apr+is%3Aclosed&per_page=99&page="+str(self.num) #第一条爬取url
        url = "https://api.github.com/repos/golang/go/pulls?q=is%3Apr+is%3Aclosed&per_page=99&page="+str(self.num) #第一条爬取url
        #添加一个爬取请求
        start_urls.append(scrapy.FormRequest(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            'Authorization': 'token ' + self.token_iter.__next__(),#这个字段为添加token字段
            }, callback=self.parse))
        return start_urls

    def yield_request(self): #定义一个生成请求函数
        #url = "https://api.github.com/repos/golang/go/issues?q=is%3Apr+is%3Aclosed&per_page=99&page="+str(self.num) #生成url
        url = "https://api.github.com/repos/golang/go/pulls?q=is%3Apr+is%3Aclosed&per_page=99&page="+str(self.num) #第一条爬取url
        #返回请求
        return Request(url,headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
                'Authorization': 'token ' + self.token_iter.__next__(),
                },callback=self.parse)

    def request_issue_url(self,url):
        return requests.get(url=url,headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
                'Authorization': 'token ' + self.token_iter.__next__(),
                })
    
    def parse_issue_url(self,response):
        json_data = json.loads(json.dumps(response.json()))
        #print(json_data)
        result = {}
        labels = []
        for i in json_data["labels"]:
            labels.append(i["name"])
        result.update({"events_url":json_data["events_url"],"labels":labels,"issue_created_at":json_data["created_at"],"issue_closed_at":json_data["closed_at"]})
        print("issue url result:"+str(result))
        return result

    def request_events_url(self,url):
        return requests.get(url=url,headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
                'Authorization': 'token ' + self.token_iter.__next__(),
                })
    
    def parse_events_url(self,response):
        json_data = json.loads(json.dumps(response.json()))
        #print(json_data)
        result = {}
        if len(json_data) != 0:
            for i in json_data:
                if "labeled" in i.keys():
                    result.update({"event_name":i["event"],"event_created_at":i["created_at"],"label_name":i["label"]["name"]})
        print("events url result:"+str(result))
        return result

    def request_diff_url(self,url):
        return requests.get(url=url,headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:36.0) Gecko/20100101 Firefox/36.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en',
                'Authorization': 'token ' + self.token_iter.__next__(),
                })
    
    def parse_diff_url(self,response):
        return len(re.findall(r"\n[\+-]\t{1}",response.text))

    #解析函数
    def parse(self, response):
        if response.status in self.handle_httpstatus_list:#如果遇见handle_httpstatus_list中出现的状态码
            self.num += 1 #num自增，相当于直接跳过，可以输出当前url到log文件
            yield self.yield_request() #产生新的请求
            return
        '''
        with open("./json.txt","w",encoding="utf-8") as f:
            f.write(json.dumps(response.json()))
        print(response.json())
        '''
        json_data = json.loads(json.dumps(response.json())) #获取json
        length = len(json_data) #获取json长度

        if length == 99:
            self.num = self.num + 1
            for PR in json_data:
                data = {}
                data['number'] = PR['number']
                data['owner'] = PR['user']['login']
                data['title'] = PR['title']
                data['created_at'] = PR['created_at']
                data['updated_at'] = PR['updated_at']
                data["closed_at"] = PR["closed_at"]
                #data["issue_url"] = issue["url"]
                data["issue_url"] = PR["issue_url"]
                data["diff_url"] = PR["diff_url"]
                if PR["updated_at"] != None:
                    #print(issue["closed_at"])
                    data["PR_lived"] = (datetime.fromisoformat(PR["updated_at"][:-1]) - datetime.fromisoformat(PR['created_at'][:-1])).total_seconds()
                data.update(self.parse_issue_url(self.request_issue_url(url=data["issue_url"])))
                data.update(self.parse_events_url(self.request_events_url(url=data["events_url"])))
                lines_changed = self.parse_diff_url(self.request_diff_url(url=data["diff_url"]))
                data.update({"lines_changed":lines_changed})
                print("data: "+str(data))
                self.output_file.write(json.dumps(data)+'\n') #输出每一行，格式也为json                    
                self.output_file.flush()
                self.csv_writer.writerow(data.values())
                self.output_csv.flush()
                time.sleep(0.2)
            yield self.yield_request() #产生新的请求

        elif length < 99: #意味着爬取到最后一页
            for PR in json_data:
                data = {}
                data['number'] = PR['number']
                data['owner'] = PR['user']['login']
                data['title'] = PR['title']
                data['created_at'] = PR['created_at']
                data['updated_at'] = PR['updated_at']
                data["closed_at"] = PR["closed_at"]
                #data["issue_url"] = issue["url"]
                data["issue_url"] = PR["issue_url"]
                data["diff_url"] = PR["diff_url"]
                if PR["updated_at"] != None:
                    #print(issue["closed_at"])
                    data["PR_lived"] = (datetime.fromisoformat(PR["updated_at"][:-1]) - datetime.fromisoformat(PR['created_at'][:-1])).total_seconds()
                data.update(self.parse_issue_url(self.request_issue_url(url=data["issue_url"])))
                data.update(self.parse_events_url(self.request_events_url(url=data["events_url"])))
                lines_changed = self.parse_diff_url(self.request_diff_url(url=data["diff_url"]))
                data.update({"lines_changed":lines_changed})
                #time.sleep(0.2)
                self.output_file.write(json.dumps(data)+'\n')
                self.output_file.flush()
                self.csv_writer.writerow(data.values())
                self.output_csv.flush()

