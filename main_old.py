import requests
import json
import re
import time
import os
import datetime
import threading
import xmltodict
import bv_dec_or_enc as bv #bv 为 Bilibili的视频BV号（这里值BV和AV互转的模块）

sign = '4e71bde0ffa847665c85f586ccb93b7e'
appkey = 'ba02c181c8820321' # 为网站外链爬虫得到

headers = {
            'cookie': "_uuid=D588BAC5-14A9-7773-8730-F2BD65E02CE780029infoc; buvid3=DACDFF53-4155-4ECE-8F94-E977D2FAFC7618542infoc; buvid_fp=DACDFF53-4155-4ECE-8F94-E977D2FAFC7618542infoc; SESSDATA=3ca7478c%2C1631165198%2C8b8c1%2A31; bili_jct=dddc742c4165e8f984d700bcd579a8b8; DedeUserID=100391403; DedeUserID__ckMd5=1192886b87b97aee; sid=d04p44f4; CURRENT_FNVAL=80; blackside_state=1; rpdid=|(J|)Y)mR|uR0J'uYulYuJkum; CURRENT_QUALITY=116; dy_spec_agreed=1; LIVE_BUVID=AUTO9716162458601286; fingerprint3=49e8e56f1ee40fda83cce50fbc6b2fc5; fingerprint=d0453b69e3c66f9a1487283ad41ef26c; fingerprint_s=12aeb0915ab8320c2fab85cded49df17; buvid_fp_plain=DACDFF53-4155-4ECE-8F94-E977D2FAFC7618542infoc; bp_video_offset_100391403=511968047381136516; bp_t_offset_100391403=511968197697652512; _dfcaptcha=b3ffe00c1624991a1cb39c431258ebd9; PVID=4",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
	    'Accept': '*/*',
	    'Accept-Encoding': 'gzip, deflate, br',
	    'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.bilibili.com'
          }

'''
definition 为视频清晰度
16 => 360P
32 => 480P
64 => 720P
80 => 1080P
74 => 720P 60FPS
116 => 1080P 60FPS
120 => 4K (据实际爬虫无效)

Cid 和 Oid 本质上是一样的！！！！
'''

sess = requests.Session()
# https://api.bilibili.com/x/player/playurl?cid=206205341&appkey=ba02c181c8820321&otype=json&type=&quality=80&qn=80&fnver=0&fnval=2&bvid=BV1xV41167qm&sign=4e71%20bde0ffa847665c85f586ccb93b7e
# http://api.bilibili.com/x/web-interface/view?bvid=BV1ft411B7mu
def GetVideoCid(id_,p=0): # 获取Cid/Oid
    if 'BV' in str(id_):
        aid = bv.dec(id_)
    else:
        aid = str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")

    search_api = "https://www.bilibili.com/widget/getPageList?aid="
    cid = sess.get(url=search_api+str(aid), headers = headers, verify=False)
    if p == 0:
        if len(json.loads(cid.text)) == 1:
            return json.loads(cid.text)[0]["cid"]
        else:
            temp_json = json.loads(cid.text)
            for i in range(len(temp_json)):
                print("第%sP,标题为：%s"%(str(temp_json[i]['page']),str(temp_json[i]['pagename'])))
            c_num = str(input("请选择需要的P:(若全选输入ALL)"))
            if c_num.upper() == "ALL":
                temp_list = []
                for i in range(len(temp_json)):
                    temp_list.append("%s@#$%s"%(str(temp_json[int(i)]['pagename']),str(temp_json[int(i)]['cid'])))
                return temp_list
            else:
                return "%s(&!%s@#$%s"%(str(c_num),str(temp_json[int(c_num)-1]['pagename']),str(temp_json[int(c_num)-1]['cid']))
    else:
        return "%s@#$%s"%(json.loads(cid.text)[p]["pagename"],json.loads(cid.text)[p]["cid"])

def GetVideoUrl(id_,cid,definition = 80): #目前没做多p批量下载
    if 'BV' in id_:
        bid = id_
    else:
        bid = bv.enc(int(str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")))
    if type(cid) == str:
        if "(&!" in cid and "@#$" in cid:
            cid = cid.split("@#$",1)[1]
        else:
            pass
    elif type(cid) == list:
        pass
    try:
        get_url_part = "https://api.bilibili.com/x/player/playurl?cid=%s&appkey=%s&otype=json&type=&quality=%s&qn=%s&fnver=0&fnval=2&bvid=%s&sign=%s"%(str(cid),appkey,str(definition),str(definition),str(bid),sign)
        req = requests.get(url=get_url_part, headers = headers, verify=False)
        json_ = json.loads(req.text)['data']
        keys = json_.keys()
    except:
        req_ = requests.session()
        url_ = "https://www.bilibili.com/video/%s"%(str(bid))
        req_ = req_.get(url=url_, headers = headers)
        pattern = '.__playinfo__=(.*)</script><script>window.__INITIAL_STATE__='
        try:
            infos = re.findall(pattern, req_.text)[0]
        except:
            try:
                pattern = '.__playinfo__=(.*)</script><script>window.__BILI_CONFIG__='
                infos = re.findall(pattern, req_.text)[0]
            except:
                return []
        json_ = json.loads(infos)['data']
        keys = json_.keys()
    
    # 不同视频类型存储视频地址的键不同，目前发现有两种，有新的类型可以提issue补充
    if 'durl' in keys:
        durl = json_['durl']
        urls = [url['url'] for url in durl]
        # urls = [url['url'] for url in durl] and [url['backup_url'] for url in durl]
    elif 'dash' in keys:
        durl = json_['dash']['video']
        #urls = [re.sub('mirror.*?\.', 'mirrorcos.', url['url']) for url in durl]
        urls = [url['baseUrl'] for url in durl]
    else:
        return []
    return urls

def GetVideoTitle(id_):
    if 'BV' in str(id_):
        bid = id_
    else:
        bid = bv.enc(int(str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")))
    
    api_info_url = "http://api.bilibili.com/x/web-interface/view?bvid=%s"%(str(bid))
    req = requests.get(url=api_info_url, headers = headers, verify=False)
    json_ = json.loads(req.text)['data']
    title = re.sub(r"[\/\\\:\*\?\"\<\>\|]","_",json_["title"])
    return title

def GetDanmu_File(id_,md=0):
    cid = GetVideoCid(id_)
    download_danmu_dir = 'download//danmu//'
    if md != 0:
        download_danmu_dir = download_danmu_dir+"md//"+str(md)+"//"
    if os.path.exists(download_danmu_dir) == False:
        os.makedirs(download_danmu_dir)
    if type(cid) == list:
        if os.path.exists(download_danmu_dir+str(GetVideoTitle(id_))) == False:
            os.makedirs(download_danmu_dir+str(GetVideoTitle(id_)))
        temp_int = 1
        for i in cid:
            download_danmu_url = "https://api.bilibili.com/x/v1/dm/list.so?oid=%s"%(i.split("@#$",1)[1])
            req = requests.get(url=download_danmu_url, headers = headers, verify=False)
            with open(download_danmu_dir+str(GetVideoTitle(id_))+"//%s-%s.xml"%(temp_int,i.split("@#$",1)[0]),"w",encoding='utf-8') as q:
                q.write(str(req.content,'utf-8')) # req.content会把gzip和deflate的内容自动解码
            temp_int += 1
    else:
        if "@#$" not in str(cid):
            download_danmu_url = "https://api.bilibili.com/x/v1/dm/list.so?oid=%s"%(str(cid))
            req = requests.get(url=download_danmu_url, headers = headers, verify=False)
            with open(download_danmu_dir+"%s.xml"%(str(GetVideoTitle(id_))),"w",encoding='utf-8') as q:
                q.write(str(req.content,'utf-8')) # req.content会把gzip和deflate的内容自动解码
        else:
            if os.path.exists(download_danmu_dir+str(GetVideoTitle(id_))) == False:
                os.makedirs(download_danmu_dir+str(GetVideoTitle(id_)))
            download_danmu_url = "https://api.bilibili.com/x/v1/dm/list.so?oid=%s"%(cid.split("(&!",1)[1].split("@#$",1)[1])
            req = requests.get(url=download_danmu_url, headers = headers, verify=False)
            with open(download_danmu_dir+str(GetVideoTitle(id_))+"//%s-%s.xml"%(cid.split("(&!",1)[0],cid.split("(&!",1)[1].split("@#$",1)[0]),"w",encoding='utf-8') as q:
                q.write(str(req.content,'utf-8')) # req.content会把gzip和deflate的内容自动解码

def xml_to_json(data):
    converteJson=xmltodict.parse(data, encoding='utf-8')
    jsonStr=json.dumps(converteJson, indent=4)
    return jsonStr

def GetAllDanmu_File(id_): #全弹幕获取目前只支持单P获取(AID/BID)
    temp_dir = 'temp'
    if os.path.exists(temp_dir) == False:
        os.makedirs(temp_dir)
    if 'BV' in id_:
        aid = bv.dec(id_)
    else:
        aid = str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")

    web_url = "https://www.bilibili.com/video/av%s"%(str(aid))
    start_time_req = requests.get(url=web_url, headers = headers, verify=False)
    try:
        req = requests.get(url="https://api.bilibili.com/x/web-interface/archive/stat?aid=%s"%(str(aid)), headers = headers, verify=False)
        if json.loads(req.text)['data']["his_rank"] != 0:
            infos = re.findall(r'</span><span>(.*)</span><span title="本日日排行数据过期后，再纳入本稿件的历史排行数据进行对比得出', start_time_req.text)[0]
        else:
            infos = re.findall(r'</span><span>(.*)</span><!----></div><div class=', start_time_req.text)[0]
    except:
        return None
    if infos:
        search_api = "https://www.bilibili.com/widget/getPageList?aid=%s"%(str(aid))
        cid = requests.get(url=search_api, headers = headers, verify=False)
        cid_num = json.loads(cid.text)[0]["cid"]
        start_time = re.findall(r"(\d{4}-\d{1,2})",infos)[0]
        time_list = []
        start_time_year = int(re.findall(r"(\d{4})",start_time)[0])
        start_time_month = int(re.findall(r"(-\d{1,2})",start_time)[0].replace("-",""))
        end_time_year = int(time.strftime('%Y',time.localtime(time.time())))
        end_time_month = int(time.strftime('%m',time.localtime(time.time())))
        if start_time_month == end_time_month and start_time_year == end_time_year:
            if len(str(start_time_month)) == 1:
                temp_start_time_month = '0'+str(start_time_month)
            else:
                temp_start_time_month = str(start_time_month)
            get_time_url = "https://api.bilibili.com/x/v2/dm/history/index?type=1&oid=%s&month=%s-%s"%(str(cid_num),str(start_time_year),str(temp_start_time_month))
            req = requests.get(url=get_time_url, headers = headers, verify=False)
            get_time_date_json = json.loads(req.text)['data']
            for time_date in get_time_date_json:
                time_list.append(time_date)
        else:
            for i in range(abs((start_time_year - end_time_year) * 12 + (start_time_month - end_time_month) * 1)+1):
                if len(str(start_time_month)) == 1:
                    temp_start_time_month = '0'+str(start_time_month)
                else:
                    temp_start_time_month = str(start_time_month)
                get_time_url = "https://api.bilibili.com/x/v2/dm/history/index?type=1&oid=%s&month=%s-%s"%(str(cid_num),str(start_time_year),str(temp_start_time_month))
                req = requests.get(url=get_time_url, headers = headers, verify=False)
                get_time_date_json = json.loads(req.text)['data']
                for time_date in get_time_date_json:
                    time_list.append(time_date)
                if start_time_month == 12:  
                    if start_time_year != end_time_year:
                        start_time_year += 1
                    start_time_month = 1
                else:
                    start_time_month += 1
            
        if os.path.exists(temp_dir+"//danmu//"+str(cid_num)) == False:
            os.makedirs(temp_dir+"//danmu//"+str(cid_num))

        for i in time_list:
            get_his_danmu_url = "https://api.bilibili.com/x/v2/dm/history?type=1&oid=%s&date=%s"%(str(cid_num),str(i))
            req = requests.get(url=get_his_danmu_url, headers = headers, verify=False)
            with open(temp_dir+"//danmu//"+str(cid_num)+"//"+i+".json","w",encoding='utf-8') as xml:
                xml.write(xml_to_json(str(req.content,'utf-8')))
        
        # file_num = len(os.listdir(temp_dir+"//danmu//"+str(cid_num)))
        file_list = os.listdir(temp_dir+"//danmu//"+str(cid_num))
        for i in range(len(os.listdir(temp_dir+"//danmu//"+str(cid_num)))-1):
            if len(file_list) == 0:
                break
            else:
                if i == 0:
                    with open(temp_dir+"//danmu//"+str(cid_num)+"//"+file_list[i],'r',encoding='utf-8') as f1:
                        temp1 = json.load(f1)
                    with open(temp_dir+"//danmu//"+str(cid_num)+".json",'w',encoding='utf-8') as f_all:
                        json.dump(temp1, f_all)
                
                with open(temp_dir+"//danmu//"+str(cid_num)+"//"+file_list[i+1],'r',encoding='utf-8') as f1:
                    temp1 = json.load(f1)
                f_all = json.load(open(temp_dir+"//danmu//"+str(cid_num)+".json",'r',encoding='utf-8'))['i']['d']
                
                f_all_list = []
                for f_all_ in f_all:
                    f_all_list.append(f_all_['@p']+"#$%^"+f_all_["#text"]) 
                t_l_1 = []
                for t1 in temp1['i']['d']:
                    t_l_1.append(t1['@p']+"#$%^"+t1["#text"])

                for te in t_l_1:
                    # try:
                    if te not in f_all_list:
                        temp_t_ = json.load(open(temp_dir+"//danmu//"+str(cid_num)+".json",'r',encoding='utf-8'))
                        temp_t_['i']['d'][len(temp_t_)+1] = {"@p":str(te.split("#$%^",1)[0]),"#text":str(te.split("#$%^",1)[1])}
                        with open(temp_dir+"//danmu//"+str(cid_num)+".json",'w',encoding='utf-8') as write_datebase:
                            json.dump(temp_t_,write_datebase)
                        f_all = json.load(open(temp_dir+"//danmu//"+str(cid_num)+".json",'r',encoding='utf-8'))['i']['d']
                        f_all_list = []
                        for f_all_ in f_all:
                            f_all_list.append(f_all_['@p']+"#$%^"+f_all_["#text"]) 
                
                write_datebase.close()

def download_video(url,filename,md=0):
    r = requests.get(url, headers=headers, stream=True, timeout=30)
    # print(r.status_code, r.headers)
    # headers = {}
 
    all_thread = 1
    # 获取视频大小
    file_size = int(r.headers['content-length'])
    # 如果获取到文件大小，创建一个和需要下载文件一样大小的文件
    if file_size:
        if ".flv" in url:
            filename = filename+".flv"
        elif ".mp4" in url:
            filename = filename+".mp4"
        elif ".m4s" in url:
            filename = filename+".m4s"
        file_dir = "download//video//"
        if md != 0:
            file_dir = file_dir+"md//"+str(md)+"//"
        if os.path.exists(file_dir) == False:
            os.makedirs(file_dir)
        fp = open(file_dir+filename, 'wb')
        fp.truncate(file_size)
        print("文件名：%s"%(str(file_dir+filename)))
        print('视频大小：' + str(int(file_size / 1024 / 1024)) + "MB")
        fp.close()
 
    # 每个线程每次下载大小为5M
    size = 5242880
    # 当前文件大小需大于5M
    if file_size > size:
        # 获取总线程数
        all_thread = int(file_size / size)
        # 设最大线程数为10，如总线程数大于10
        # 线程数为10
        if all_thread > 10:
            all_thread = 10
 
    part = file_size // all_thread
    threads = []
 
    starttime = datetime.datetime.now().replace(microsecond=0)
    for i in range(all_thread):
        # 获取每个线程开始时的文件位置
        start = part * i
        # 获取每个文件结束位置
        if i == all_thread - 1:
            end = file_size
        else:
            end = start + part
        if i > 0:
            start += 1
        headers_ = headers.copy()
        headers_['Range'] = "bytes=%s-%s" % (start, end)
        t = threading.Thread(target=Handler, name='th-' + str(i),
                             kwargs={'start': start, 'end': end, 'url': url, 'filename': file_dir+filename, 'headers': headers_})
        t.setDaemon(True)
        threads.append(t)
    # 线程开始
    for t in threads:
        time.sleep(0.2)
        t.start()
 
    # 等待所有线程结束
    for t in threads:
        t.join()
 
    endtime = datetime.datetime.now().replace(microsecond=0)
    print('用时：%s' % (endtime - starttime))
 
 
def Handler(start, end, url, filename, headers={}):
    tt_name = threading.current_thread().getName()
    print(tt_name + ' is begin')
    r = requests.get(url, headers=headers, stream=True)
    total_size = end - start
    downsize = 0
    startTime = time.time()
    with open(filename, 'r+b') as fp:
        fp.seek(start)
        var = fp.tell()
        for chunk in r.iter_content(204800):
            if chunk:
                fp.write(chunk)
                downsize += len(chunk)
                line = tt_name + '-downloading %d KB/s - %.2f MB， 共 %.2f MB'
                line = line % (
                    downsize / 1024 / (time.time() - startTime), downsize / 1024 / 1024,
                    total_size / 1024 / 1024)
                print(line, end='\r')

def GetMd_Aid_and_title(season_id):
    get_url = "https://api.bilibili.com/pgc/web/season/section?season_id=%s"%(str(season_id))
    req = requests.get(url=get_url, headers = headers, verify=False)
    temp_json = json.loads(req.text)['result']['main_section']['episodes']
    temp_list = []
    for i in range(len(temp_json)):
        temp_list.append({"aid":"av"+str(temp_json[i]["aid"]),"cid":temp_json[i]["cid"],"title":temp_json[i]["long_title"]})
    return temp_list

def download_md_video(aid_title_list,season_id,p=None):
    ii = 1
    for i in aid_title_list:
        if not p:
            download_video(GetVideoUrl(i["aid"],i["cid"])[0],i["title"],md=int(season_id))
        elif p:
            if ii >= p:
                download_video(GetVideoUrl(i["aid"],i["cid"])[0],i["title"],md=int(season_id))
            elif ii < p:
                ii += 1
            
    
def download_md_danmu(season_id):
    download_danmu_dir = "download//danmu//md//"+str(season_id)+"//"
    if os.path.exists(download_danmu_dir) == False:
        os.makedirs(download_danmu_dir)
    for i in GetMd_Aid_and_title(season_id):
        download_danmu_url = "https://api.bilibili.com/x/v1/dm/list.so?oid=%s"%(str(i["cid"]))
        req = requests.get(url=download_danmu_url, headers = headers, verify=False)
        with open(download_danmu_dir+"%s.xml"%(str(re.sub(r"[\/\\\:\*\?\"\<\>\|]","_",i["title"]))),"w",encoding='utf-8') as q:
            q.write(str(req.content,'utf-8')) # req.content会把gzip和deflate的内容自动解码

if __name__=='__main__':
    aid_or_bid = input("aid/bvid :")
    download_video(GetVideoUrl(aid_or_bid,GetVideoCid(aid_or_bid))[0],GetVideoTitle(aid_or_bid)) #下载单视频
    
    
