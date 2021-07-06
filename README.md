# B站视频/弹幕下载器 (Python)

B站视频/弹幕下载器

**该程序仅供学习使用 使用Apache license 2.0许可证**

## 文件介绍

* `main.py`：主程序
* `configuration.json`：默认配置文件
* `bv_dec_or_enc.py`：AV/BV号互转 Python 库 来自[知乎 - 如何看待2020年3月23日bilibili将稿件av号变更为字母数字格式的"BV号"？](https://www.zhihu.com/question/381784377/answer/1099438784)

**跪求Star Orz...**
## 主程序内函数介绍
|函数名|用途简介|是否需要参数|所需参数|
|-|-|-|-|
|GetVideoCid|获取Cid/Oid|是|id_, m, p|
|GetVideoUrl|获取B站视频地址|是|id_, definition|
|GetVideoTitle|获取视频标题|是|id_|
|GetDanmu_File|下载弹幕文件|是|id_, md， download_danmu_dir|
|download_video|下载视频文件(多线程) [来源](https://www.jb51.net/article/174321.htm)|是|url, filename, md, file_dir|
|Handler|多线程下载启动函数 [来源](https://www.jb51.net/article/174321.htm)|是|start, end, url, filename, headers|
|GetMd_Aid_and_title|获取番剧各集的AV号和标题|是|_id|
|download_md_video|下载番剧视频文件|是|aid_title_list, _id, p|
|check_is_media_id|检测番剧代号是season_id还是media_id|是|id|
|GetMD_Title|获取番剧名字|是|id|
|media_id_to_season_id|将media_id转为season_id|是|media_id|
|download_md_danmu|下载番剧弹幕文件|是|id|
|ep_to_season_id|番剧各集的ep代号转为season_id或BV(用户选择)|是|_id|
|auto_download_video|自动匹配用户输入并自动下载视频文件|是|video_url|
|auto_download_video_danmu|自动匹配用户输入并自动下载弹幕文件|是|video_url|
|LoadConfiguration|加载本地配置文件|否||
|menu|主程序菜单|否||




