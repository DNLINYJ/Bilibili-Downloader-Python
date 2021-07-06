import requests
import json
import re
import time
import os
import platform
import sys
import datetime
import threading
import bv_dec_or_enc as bv #bv 为 Bilibili的视频BV号（这里值BV和AV互转的模块）

#关闭requests模块的InsecureRequestWarning警告提示
#from：https://www.cnblogs.com/milian0711/p/6836384.html
#此处 VS Code 报错为正常现象
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

sign = '4e71bde0ffa847665c85f586ccb93b7e'
appkey = 'ba02c181c8820321' # 为网站外链爬虫得到

global video_file_situation
global danmu_file_situation
video_file_situation = 0
danmu_file_situation = 0

headers = {
            'cookie': "SESSDATA=3ca7478c%2C1631165198%2C8b8c1%2A31;",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.bilibili.com'
          }

def GetVideoCid(id_,m=0,p=0): 
    """
        获取Cid/Oid\n

        id_ BV/AV号\n
        m 模式（默认为0[默认]，1为[返回全部分P]）\n
        p 指定返回分P （默认为0[不指定]）\n
        
        (1)单P返回格式: (str)
            "视频cid号"

        (2)多P下载所有返回格式： (dict)
            {"视频标题1":"视频cid号1","视频标题2":"视频cid号2",...,"视频标题n":"视频cid号n"}

        (2)多P下载单P返回格式： (list)
            ["视频P数","视频标题","视频cid号"]

        temp_json['videos']['pages'][i]['part'] 或 json.loads(cid.text)['videos']['pages'][i]['part'] 是分P标题 i是视频P数\n
        Cid 和 Oid 本质上是一样的！！！！
    """

    if 'BV' in str(id_): #将BV/AV号转换为BV号
        bvid = id_
    else:
        bvid = bv.enc(int(str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")))

    search_api = f"https://api.bilibili.com/x/player/pagelist?bvid={str(bvid)}"
    cid = requests.get(url=search_api, headers = headers, verify=False)

    if p == 0: #当没有指定P数时（默认）

        if len(json.loads(cid.text)['data']) == 1: #当只有一个视频时
            return str(json.loads(cid.text)['data'][0]["cid"])

        else: #当有多个视频时
            if m == 1: #返回全部分P(函数传入)
                temp_json = json.loads(cid.text)
                temp_dict = {}
                for i in range(len(temp_json["data"])):
                    temp_dict[temp_json['data'][i]['part']] = str(temp_json['data'][i]['cid'])
                return temp_dict

            temp_json = json.loads(cid.text)
            for i in range(len(temp_json['data'])): #输出P数和各自对应的标题
                print("第%sP,标题为：%s"%(str(temp_json['data'][i]["page"]),str(temp_json['data'][i]['part'])))
                # temp_json['data'][i]["page"] 视频P数
                # temp_json['data'][i]['part'] 视频标题

            c_num = str(input("请选择需要的P:(若全选输入ALL)")) #c_num 为视频P数 

            if c_num.upper() == "ALL":
                temp_dict = {}
                for i in range(len(temp_json["data"])):
                    temp_dict[temp_json['data'][i]['part']] = str(temp_json['data'][i]['cid'])
                return temp_dict
            else:
                return [str(c_num),str(temp_json['data'][int(c_num)-1]['part']),str(temp_json['data'][int(c_num)-1]['cid'])]

    else:   # 指定P数时 
            # 多P下载单P返回格式： (list) 
            # ["视频P数","视频标题","视频cid号"]
        return [p, json.loads(cid.text)['data'][int(p)-1]['part'], json.loads(cid.text)['data'][int(p)-1]["cid"]]

def GetVideoUrl(id_,definition = 120): #目前没做多p批量下载
    '''
    获取B站视频地址\n
    definition 为视频清晰度:
        16 => 360P
        32 => 480P
        64 => 720P
        80 => 1080P
        74 => 720P 60FPS
        116 => 1080P 60FPS
        120 => 4K (据实际爬虫无效)
    '''
    if 'BV' in id_:
        bid = id_
    else:
        bid = bv.enc(int(str(id_).replace("av","").replace("AV","").replace("aV","").replace("Av","")))

    cid = GetVideoCid(id_)
    if type(cid) == list: # GetVideoCid 的第二种情况
        cid = cid[2] 
    elif type(cid) == dict: # GetVideoCid 的第三种情况
        pass

    try:
        get_url_part = "https://api.bilibili.com/x/player/playurl?cid=%s&appkey=%s&otype=json&type=&quality=%s&qn=%s&fnver=0&fnval=2&bvid=%s&sign=%s"%(str(cid),appkey,str(definition),str(definition),str(bid),sign)
        req = requests.get(url=get_url_part, headers = headers, verify=False)
        json_ = json.loads(req.text)['data']
        keys = json_.keys()
    except:
        url_ = "https://www.bilibili.com/video/%s"%(str(bid))
        req = requests.get(url=url_, headers = headers, verify=False)
        pattern = '.__playinfo__=(.*)</script><script>window.__INITIAL_STATE__='
        try:
            infos = re.findall(pattern, req.text)[0]
        except:
            try:
                pattern = '.__playinfo__=(.*)</script><script>window.__BILI_CONFIG__='
                infos = re.findall(pattern, req.text)[0]
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
        # urls = [re.sub('mirror.*?\.', 'mirrorcos.', url['url']) for url in durl]
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

def GetDanmu_File(id_, md=0, download_danmu_dir = 'download//danmu//'):
    """
    id AV号/BV号\n
    md 是否为番剧（默认为0[否]）\n

    """
    cid = GetVideoCid(id_)

    if type(danmu_file_situation) == list:
        download_danmu_dir = danmu_file_situation[1]
    
    if md != 0:
        download_danmu_dir = download_danmu_dir+"md//"+str(md)+"//"
    if os.path.exists(download_danmu_dir) == False:
        os.makedirs(download_danmu_dir)

    if type(cid) == dict: #多P下载所有P弹幕 
        if os.path.exists(download_danmu_dir+str(GetVideoTitle(id_))) == False:
            os.makedirs(download_danmu_dir+str(GetVideoTitle(id_)))
        temp_int = 1
        for i in list(cid.keys()):
            download_danmu_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid[i]}"
            req = requests.get(url=download_danmu_url, headers = headers, verify=False)
            with open(f"{download_danmu_dir}{str(GetVideoTitle(id_))}//{temp_int}-{i}.xml","wb+") as q:
                q.write(req.content) # req.content会把gzip和deflate的内容自动解码
            temp_int += 1

    elif type(cid) == str: #单P下载弹幕
        download_danmu_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={str(cid)}"
        req = requests.get(url=download_danmu_url, headers = headers, verify=False)
        with open(f"{download_danmu_dir}{str(GetVideoTitle(id_))}.xml","wb+") as q:
            q.write(req.content) # req.content会把gzip和deflate的内容自动解码

    elif type(cid) == list: #多P下载单P弹幕 
        if os.path.exists(download_danmu_dir+str(GetVideoTitle(id_))) == False:
            os.makedirs(download_danmu_dir+str(GetVideoTitle(id_)))
        download_danmu_url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={str(cid[2])}"
        req = requests.get(url=download_danmu_url, headers = headers, verify=False)
        with open(f"{download_danmu_dir}{str(GetVideoTitle(id_))}//{str(cid[0])}-{str(cid[1])}.xml","wb+") as q:
            q.write(req.content) # req.content会把gzip和deflate的内容自动解码

def download_video(url, filename, md=0, file_dir = "download//video//"):
    r = requests.get(url, headers=headers, stream=True, timeout=30)

    if type(video_file_situation) == list:
        file_dir = video_file_situation[1]
 
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

def GetMd_Aid_and_title(_id):
    temp_v = check_is_media_id(_id)
    if type(temp_v) == list:
        if temp_v[1] == "md":
            season_id = media_id_to_season_id(_id)
        else:
            season_id = _id
    elif temp_v == True:
        season_id = media_id_to_season_id(_id)
    elif temp_v == False:
        season_id = _id

    get_url = "https://api.bilibili.com/pgc/web/season/section?season_id=%s"%(str(season_id))
    req = requests.get(url=get_url, headers = headers, verify=False)
    temp_json = json.loads(req.text)['result']['main_section']['episodes']
    temp_list = []
    for i in range(len(temp_json)):
        temp_list.append({"aid":"av"+str(temp_json[i]["aid"]),"cid":temp_json[i]["cid"],"title":temp_json[i]["long_title"]})
    return temp_list

def download_md_video(aid_title_list,_id,p=None):
    ii = 1
    temp_v = check_is_media_id(_id)
    if type(temp_v) == list:
        if temp_v[1] == "md":
            season_id = media_id_to_season_id(_id)
        else:
            season_id = _id
    elif temp_v == True:
        season_id = media_id_to_season_id(_id)
    elif temp_v == False:
        season_id = _id
    for i in aid_title_list:
        if not p:
            download_video(GetVideoUrl(i["aid"])[0],f'{str(ii)}-{i["title"]}',md=str(season_id)+"-"+GetMD_Title(season_id))
            ii += 1
        elif p:
            if ii >= p:
                download_video(GetVideoUrl(i["aid"])[0],i["title"],md=str(season_id)+"-"+GetMD_Title(season_id))
            elif ii < p:
                ii += 1
            
def check_is_media_id(id):
    url = f"https://www.bilibili.com/bangumi/media/md{str(id)}"
    req = requests.get(url=url, headers = headers, verify=False)
    if req.status_code == 200:
        url = f"https://www.bilibili.com/bangumi/play/ss{str(id)}"
        req_ = requests.get(url=url, headers = headers, verify=False)
        if req_.status_code == 200:
            url = f"https://api.bilibili.com/pgc/review/user?media_id={str(id)}"
            md_req = requests.get(url=url, headers = headers, verify=False)
            url = f"https://www.bilibili.com/bangumi/play/ss{str(id)}"
            ss_req = requests.get(url=url, headers = headers, verify=False)
            if json.loads(md_req.text)["result"]["media"]["title"] == re.findall(r'class="media-title">([\d\D]*?)</a>',ss_req.text)[0]:
                return False
            print("——————————————————————————————————————————————————————————————————————————————————————————")
            print(f'1.{json.loads(md_req.text)["result"]["media"]["title"]}')
            temp_str = re.findall(r'class="media-title">([\d\D]*?)</a>',ss_req.text)[0]
            print(f'2.{temp_str}')
            temp_input = input("请问您想下载哪个番剧(输入数字):")
            if str(temp_input) == "1":
                return [True,"md"]
            else:
                return [True,"ss"]
        else:
            return True
    return False

def GetMD_Title(id):
    temp = check_is_media_id(id)
    if type(temp) == list:
        if temp[1] == "ss":
            url = f"https://www.bilibili.com/bangumi/play/ss{str(id)}"
            req = requests.get(url=url, headers = headers, verify=False)
            return re.findall(r'class="media-title">([\d\D]*?)</a>',req.text)[0]
        else:
            url = f"https://api.bilibili.com/pgc/review/user?media_id={str(id)}"
            req = requests.get(url=url, headers = headers, verify=False)
            return json.loads(req.text)["result"]["media"]["title"]
    else:
        if temp == True:
            url = f"https://api.bilibili.com/pgc/review/user?media_id={str(id)}"
            req = requests.get(url=url, headers = headers, verify=False)
            return json.loads(req.text)["result"]["media"]["title"]
        else:
            url = f"https://www.bilibili.com/bangumi/play/ss{str(id)}"
            req = requests.get(url=url, headers = headers, verify=False)
            return re.findall(r'class="media-title">([\d\D]*?)</a>',req.text)[0]

def media_id_to_season_id(media_id):
    url = f"https://api.bilibili.com/pgc/review/user?media_id={str(media_id)}"
    req = requests.get(url=url, headers = headers, verify=False)
    return json.loads(req.text)["result"]["media"]["season_id"]

def download_md_danmu(id):
    temp_v = check_is_media_id(id)
    if type(temp_v) == list:
        if temp_v[1] == "md":
            season_id = media_id_to_season_id(id)
        else:
            season_id = id
    elif temp_v == True:
        season_id = media_id_to_season_id(id)
    elif temp_v == False:
        season_id = id

    download_danmu_dir = "download//danmu//md//" + f"{str(season_id)} - {str(GetMD_Title(season_id))}"+"//"
    if os.path.exists(download_danmu_dir) == False:
        os.makedirs(download_danmu_dir)

    temp_list = GetMd_Aid_and_title(season_id)
    for i in range(len(temp_list)):
        download_danmu_url = f'https://api.bilibili.com/x/v1/dm/list.so?oid={str(temp_list[i]["cid"])}'
        req = requests.get(url=download_danmu_url, headers = headers, verify=False)
        with open(download_danmu_dir + str(i + 1) + "-" + str(re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", temp_list[i]["title"])) + '.xml', "w", encoding='utf-8') as q:
            q.write(str(req.content,'utf-8')) # req.content会把gzip和deflate的内容自动解码

def ep_to_season_id(_id):
    url = "https://api.bilibili.com/pgc/view/web/season?ep_id=" + str(_id)
    req = requests.get(url=url, headers = headers, verify=False)
    user_choose = ""
    rr = r"</script><script>window.__INITIAL_STATE__=([\d\D]*?);\(function"
    title = json.loads(re.findall(rr, requests.get(url="https://www.bilibili.com/bangumi/play/ep" + str(_id), headers = headers, verify=False).text)[0])["h1Title"].split("：", 1)[1]
    while user_choose == "":
        print(f"您是想下载本话 {title} 吗?(Y/N)")
        user_choose = input(">>").upper()
        if user_choose == "Y":
            return [ json.loads(req.text)["result"]["episodes"][int(re.findall(r"\d+", title)[0]) - 1]["bvid"] ]
        else:
            print("您是想下载整个番剧吗?(Y/N)")
            user_choose = input(">>").upper()
            if user_choose == "Y":
                return json.loads(req.text)["result"]["season_id"]
            else:
                user_choose = ""
        

def auto_download_video(video_url):
    base_url_list = [
        "https://www.bilibili.com/bangumi/play/ss",
        "https://www.bilibili.com/bangumi/media/md",
        "https://www.bilibili.com/video/",
        "https://www.bilibili.com/bangumi/play/ep"
    ]
    if "http" in video_url:
        for i in range(len(base_url_list)):
            if base_url_list[i] in video_url:
                if i == 0 or i == 1:
                    _id = str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/","")
                    download_md_video(GetMd_Aid_and_title(_id), _id)
                    break
                elif i == 3:
                    season_id = ep_to_season_id(str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/",""))
                    if type(season_id) == list:
                        download_video(GetVideoUrl(season_id[0])[0], GetVideoTitle(season_id[0]))
                    else:
                        download_md_video(GetMd_Aid_and_title(season_id), season_id)
                    break
                else:
                    aid_or_bid = str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/","")
                    download_video(GetVideoUrl(aid_or_bid)[0], GetVideoTitle(aid_or_bid)) #下载单视频
                    break
    else:
        if "BV" in video_url:
            try:
                download_video(GetVideoUrl(video_url)[0], GetVideoTitle(video_url))
            except:
                print("输入了不受支持的链接/字符串，请重新输入。")
        elif "AV" in video_url.upper():
            try:
                download_video(GetVideoUrl(video_url)[0], GetVideoTitle(video_url))
            except:
                print("输入了不受支持的链接/字符串，请重新输入。")

def auto_download_video_danmu(video_url):
    base_url_list = [
        "https://www.bilibili.com/bangumi/play/ss",
        "https://www.bilibili.com/bangumi/media/md",
        "https://www.bilibili.com/video/",
        "https://www.bilibili.com/bangumi/play/ep"
    ]
    if "http" in video_url:
        for i in range(len(base_url_list)):
            if base_url_list[i] in video_url:
                if i == 0 or i == 1:
                    _id = str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/","")
                    download_md_danmu(_id)
                    break
                elif i == 3:
                    season_id = ep_to_season_id(str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/",""))
                    download_md_danmu(season_id)
                    break
                else:
                    aid_or_bid = str(video_url).replace(base_url_list[i],"").split("?",1)[0].replace("/","")
                    GetDanmu_File(aid_or_bid)
                    break
    else:
        if "BV" in video_url:
            try:
                GetDanmu_File(video_url.split("?",1)[0].replace("/",""))
            except:
                print("输入了不受支持的链接/字符串，请重新输入。")
        elif "AV" in video_url.upper():
            try:
                download_video(video_url.split("?",1)[0].replace("/",""))
            except:
                print("输入了不受支持的链接/字符串，请重新输入。")


def LoadConfiguration():
    try:
        with open("configuration.json", "r", encoding="utf-8") as f:
            configuration = json.load(f)
        if configuration["video_file_path"] != "download//video//":
            video_file_situation = [1, configuration["video_file_path"]]
        if configuration["danmu_file_path"] != "download//danmu//":
            danmu_file_situation = [1, configuration["danmu_file_path"]]
        print("读取配置文件成功。")
    except:
        print("读取配置文件失败！使用默认配置。")

def menu():
    system_platform = platform.system()
    if system_platform == "Windows":
        clean_command = "cls"
    elif system_platform == "Linux":
        clean_command = "clear"
    else:
        clean_command = "clear"

    while True:
        print("欢迎使用Bilibili下载器╰(*°▽°*)╯ 作者:菠萝小西瓜")
        print("1) 下载视频")
        print("2) 下载弹幕")
        print("3) 退出")
        user_choose = input(">>")

        if user_choose == "1":
            url = input("请输入B站视频链接或 AV/BV 号:")
            auto_download_video(url)
            input("请按任意键继续...")
            os.system(clean_command)

        elif user_choose == "2":
            url = input("请输入B站视频链接或 AV/BV 号:")
            auto_download_video_danmu(url)
            input("请按任意键继续...")
            os.system(clean_command)

        elif user_choose == "3":
            sys.exit(0)

        else:
            print("请输入正确的选项!")
            input("请按任意键继续...")
            os.system(clean_command)

if __name__=='__main__':
    LoadConfiguration()
    menu()
