from datetime import timedelta
import os
import pickle
import sys

from flask import Flask, render_template, send_file

from app.DataBase import msg_db
from app.DataBase.package_msg import PackageMsg
from app.analysis import analysis
from app.person import Contact, Me
from app.util.emoji import get_most_emoji
from app.web_ui.util import *
from chinese_calendar import is_holiday

app = Flask(__name__)

contact: Contact = None
contacts = None

def save_pickle(data, file_path):
    if os.path.exists(file_path):
        return
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def load_pickle(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            loaded_list = pickle.load(f)
            return loaded_list
    return None

def get_y_mar(s, a,b,c,d):
    if "," in s:
        return a,b
    else:
        return c,d

def get_rank_list(bg_image, pos, right, wxid_to_num, wxid_to_room_name, unit="条",limit=4, tag=""):
    res = []
    msg_sum = 0
    for key in wxid_to_num:
        # print(wxid_to_name[key]["conRemark"], wxid_to_num[key])
        msg_sum += wxid_to_num[key]
        if key not in wxid_to_room_name:
            continue
        res.append(key)
    res.sort(key=lambda k : wxid_to_num[k], reverse=True)

    iter_len = min(limit, len(res))
    x = pos[0]
    y = pos[1]
    space = 20

    if len(tag) > 0:
        bg_image, width,height = draw_text_rank(bg_image, tag, 25, (320,y), font_width="bold",align="center",v_align="center",color="white")
        y += height+30
    else:
        y += 30
    for i in range(iter_len):
        wxid = res[i]
        avatar_path = wxid_to_room_name[wxid].avatar_path
        person_num = wxid_to_num[wxid]
        person_name = wxid_to_room_name[wxid].nickName
        person_rate = int(person_num / msg_sum * 100)
        # print(wxid_to_name[wxid]["conRemark"], wxid_to_num[wxid])
        ava_img = Image.open(avatar_path)
        bg_image, width,height = draw_text_rank(bg_image, str(i+1)+".", 30, (x,y), align="leaf",v_align="center",color="white")
        bg_image = draw_avatar(bg_image,ava_img, (x+50,y), (60,60), 2, v_align="center")


        bg_image, width, height = draw_multi_text_rank(bg_image, [str(person_rate),"%，",str(person_num), unit], font_size_list=[30,20,30,20], pos=(right,y),
                            color_list=["white", "white","white", "white"],
                             font_width_list=["bold", "normal","bold", "normal"],
                             space=[0,10,0,0])
        right_width = width
        name_x = x+50+60+20
        bg_image, width,height = draw_text_rank(bg_image, person_name, 25, (name_x,y), align="leaf",v_align="center",color="white",max_width=right-name_x-right_width-10)
        # bg_image, width,height = draw_text_rank(bg_image, str(person_num), 30, (right-width,y), align="right",v_align="center",color="white")
        # right_margin = right_margin + width
        # bg_image, width,height = draw_text_rank(bg_image, "%", 20, (right-width-right_margin-20, y), align="right",v_align="center",color="white")
        # right_margin = right_margin + width +20
        # bg_image, width,height = draw_text_rank(bg_image, str(person_rate), 30, (right-right_margin, y), align="right",v_align="center",color="white")
        # bg_image = draw_avatar(bg_image, Image.open(avatar_path),(320-175//2,112),(175,175),5)
        y += space+60
    return bg_image

@app.route("/")
def index():
    # 渲染模板，并传递图表的 HTML 到模板中
    return "index.html"

def christmasForRoom():
    """ 
        a[0]: localId,
        a[1]: talkerId, （和strtalker对应的，不是群聊信息发送人）
        a[2]: type,
        a[3]: subType,
        a[4]: is_sender,
        a[5]: timestamp,
        a[6]: status, （没啥用）
        a[7]: str_content,
        a[8]: str_time, （格式化的时间）
        a[9]: msgSvrId,
        a[10]: BytesExtra,
        a[11]: CompressContent,
        a[12]: msg_sender, （ContactPC 或 ContactDefault 类型，这个才是群聊里的信息发送人，不是群聊或者自己是发送者没有这个字段） 
    """
    year = '2023'
    room_name = contact.nickName
    # file_path = f'./data/pickle/{contact.wxid}'
    # messages = load_pickle(file_path)
    # if messages is None:
    #     messages = PackageMsg().get_package_message_by_wxid(contact.wxid)
    # save_pickle(messages, file_path)
    messages = PackageMsg().get_package_message_by_wxid(contact.wxid)
    messages_len = len(messages)
    if messages_len < 10:
        return
    def page_one():
        print("正在生成第一页")
        output_path = f'./data/room/{room_name}-1.png'
        background_image_path = './data/pic/wechat.png'
        background_image : Image = Image.open(background_image_path)
        # 头像部分
        background_image = draw_avatar(background_image, Image.open(contact.avatar_path), (320-175//2,50), (175,175), 5)
        background_image = draw_text_emoji(background_image, room_name, 40, (320, 250), align="center", max_width=600)
        # 内容部分
        #  建立时间
        firstWordDict = {}
        firstTime = None
        for message in messages:
            msg_sender = message[12]
            _wxid = msg_sender.wxid
            if firstTime is None or firstTime > message[5]:
                firstTime = message[5]
            if message[2] != 1:
                continue
            if _wxid not in firstWordDict or firstWordDict[_wxid][5] > message[5]:
                firstWordDict[_wxid] = message
        first_day = timestamp_to_day(firstTime)
        first_datetime = datetime.fromtimestamp(firstTime)
        current_date = datetime.now()
        difference = current_date - first_datetime
        days_passed = difference.days
        x = 60
        y = 300
        space = 30
        # 认识天数
        background_image, height = draw_multi_text(background_image, ["本群已经建立至少",str(days_passed),"天了"], [30,55,30],(x,y),
                                    color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                    space=[5,5,0])
        y += height+space
        # 认识日期
        background_image, height = draw_multi_text(background_image, ["从",first_day,"开始"], [30,40,30],(x,y),
                                        color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                        space=[5,5,0])
        total_msg_len_str = "{:,}".format(messages_len)
        if "," in total_msg_len_str:
            y+=height+space-20
            top_mar = 10
        else:
            y+=height+space-15
            top_mar = 0
        # 消息总数
        background_image, height = draw_multi_text(background_image, ["本群有",total_msg_len_str,"条聊天信息"], [30,55,30],(x,y),
                                        color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                        space=[5,5,0],
                                        top_margin=[0,top_mar,0])
        y += height + space
        # 说过的第一句话
        background_image, height = draw_multi_text(background_image, ["你们说过的第一句话分别是"], [30],(x,y),
                                        color_list=["white"],font_width_list=["normal"],
                                        space=[5])
        y += height + space
        for _wxid, _message in firstWordDict.items():
            nickName = contacts[_wxid].nickName
            text = nickName + ":" + _message[7]
            background_image = draw_text_emoji(background_image, text, 30, (x, y), max_width=640-x)
            y += 50
        background_image.save(output_path)
        print("生成完成，路径在：", f"生成结果 {output_path}")

    def page_two():
        print("正在生成第二页")
        output_path = f'./data/room/{room_name}-2.png'
        background_image_path = './data/pic/txt.png'
        background_image = Image.open(background_image_path)
        background_image = draw_text(background_image, f"『{year}年度·话痨』", 40, (320, 40), align="center", max_width=500)

        #文本消息
        x = 40
        y = 100
        space = 35
        # 年度消息
        # background_image, height = draw_multi_text(background_image, ["在这一年"], [30],(x,y),
        #                             color_list=["white"],font_width_list=["normal"],
        #                             space=[5])
        year_msg_len_str = "{:,}".format(messages_len)
        y,top_mar = get_y_mar(year_msg_len_str, y+space-25, 10, y+space-20, 0)
        background_image, height = draw_multi_text(background_image, ["这一年本群有",year_msg_len_str,"条聊天信息"], [30,55,30],(x,y),
                                        color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                        space=[5,5,0],
                                        top_margin=[0,top_mar,0])
        # 文本信息
        txt_time = 0
        word_len = 0
        txt_rank = {}
        for message in messages:
            wxid = message[12].wxid
            if message[2] == 1:
                txt_time += 1
                word_len += len(message[7])
            if wxid not in txt_rank and wxid in contacts:
                txt_rank[wxid] = 0
            if wxid in wxid in contacts:
                txt_rank[wxid] += 1
        txt_time = "{:,}".format(txt_time)
        y,top_mar = get_y_mar(txt_time, y+height+space-20, 10, y+height+space-20, 0)
        background_image, height = draw_multi_text(background_image, ["其中，文本信息有",txt_time,"条"], [30,55,30],(x,y),
                                    color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                    space=[5,5,0],
                                    top_margin=[0,top_mar,0])
        
        word_len_str = "{:,}".format(word_len)
        y,top_mar = get_y_mar(word_len_str, y+height+space-20, 10, y+height+space-15, 0)
        background_image, height = draw_multi_text(background_image, ["共计",word_len_str,"个字"], [30,55,30],(x,y),
                                    color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                    space=[5,5,0],
                                    top_margin=[0,top_mar,0])
        y += height + space
        maxx_wxid = max(txt_rank, key=txt_rank.get)
        minn_wxid = min(txt_rank, key=txt_rank.get)
        offset = 60
        ava_img = Image.open(contacts[maxx_wxid].avatar_path)
        background_image = draw_avatar(background_image, ava_img, (x+offset,y), (60, 60), 2)
        background_image = draw_text(background_image, "摸鱼之王", 30, (x + 70 + offset, y+15), max_width=600, font_width='')
        ava_img = Image.open(contacts[minn_wxid].avatar_path)
        background_image = draw_avatar(background_image, ava_img, (x+300+offset,y), (60, 60), 2)
        background_image = draw_text(background_image, "感情淡了", 30, (x + 370 + offset, y+15), max_width=600, font_width='')

        y += 75
        background_image = get_rank_list(background_image, (50, y), 600, txt_rank, contacts, limit=min(len(txt_rank), 7))

        background_image.save(output_path)
        print("生成完成，路径在：", f"生成结果 {output_path}")

    def page_three():
        print("正在生成第三页")
        output_path = f'./data/room/{room_name}-3.png'
        background_image_path = './data/pic/txt.png'
        background_image = Image.open(background_image_path)
        background_image = draw_text(background_image, f"『{year}年度·家人』", 40, (320, 40), align="center", max_width=500)

        #文本消息
        x = 40
        y = 100
        space = 35
        # 平均消息
        holiday_tot, holiday_num = 0, 0
        firstTime = None
        txt_time = 0
        txt_rank = {}
        for message in messages:
            wxid = message[12].wxid
            if wxid not in contacts:
                continue
            if firstTime is None or firstTime > message[5]:
                firstTime = message[5]
            txt_time += 1
            if is_holiday(datetime.fromtimestamp(message[5])):
                holiday_tot += 1
                if wxid not in txt_rank:
                    txt_rank[wxid] = 0
                txt_rank[wxid] += 1
        first_day = datetime.fromtimestamp(firstTime)
        end_date = datetime(2023, 12, 31)
        tot_day = (end_date - first_day).days
        while first_day <= end_date:
            holiday_num += 1
            first_day += timedelta(days=1)

        #  每天平均条数
        data1 = "{:,}".format(txt_time//tot_day)
        y,top_mar = get_y_mar(data1, y+space-25, 10, y+space-20, 0)
        background_image, height = draw_multi_text(background_image, ["本群平均每天有",data1,"条消息"], [30,55,30],(x,y),
                                        color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                        space=[5,5,0],
                                        top_margin=[0,top_mar,0])
        # 节假日平均天数
        data2 = "{:,}".format(holiday_tot//holiday_num)
        y,top_mar = get_y_mar(data2, y+height+space-20, 10, y+height+space-20, 0)
        background_image, height = draw_multi_text(background_image, ["节假日平均只有",data2,"条"], [30,55,30],(x,y),
                                    color_list=["white", "white", "white"],font_width_list=["normal", "bold", "normal"],
                                    space=[5,5,0],
                                    top_margin=[0,top_mar,0])
        space = 25
        y += height + space
        maxx_wxid = max(txt_rank, key=txt_rank.get)
        minn_wxid = min(txt_rank, key=txt_rank.get)
        offset = 60
        img_height = 50
        ava_img = Image.open(contacts[maxx_wxid].avatar_path)
        background_image = draw_avatar(background_image, ava_img, (x+offset,y), (60, 60), 2)
        background_image = draw_text(background_image, "真正的家人", 30, (x + 70 + offset, y+15), max_width=600, font_width='')
        y += img_height + space
        ava_img = Image.open(contacts[minn_wxid].avatar_path)
        background_image = draw_avatar(background_image, ava_img, (x+offset,y), (60, 60), 2)
        background_image = draw_text(background_image, "群友只是工作搭子", 30, (x + 70 + offset, y+15), max_width=600, font_width='')
        y += img_height + space
        # for smz
        ava_img = Image.open(contacts['wxid_yi5jfmuk23x822'].avatar_path)
        background_image = draw_avatar(background_image, ava_img, (x+offset,y), (60, 60), 2)
        background_image = draw_text(background_image, "疑似小号", 30, (x + 70 + offset, y+15), max_width=600, font_width='')
        y += img_height + space
        background_image = get_rank_list(background_image, (50, y), 600, txt_rank, contacts, limit=min(len(txt_rank), 7))

        background_image.save(output_path)
        print("生成完成，路径在：", f"生成结果 {output_path}")
    
    def page_img():
        print("正在生成表情包页")
        output_path = f'./data/room/{room_name}-img.png'
        bimg_num = 0
        bimg_to_num = {}
        bimg_rank = {}
        emoji_msgs = msg_db.get_messages_by_type(contact.wxid, 47, year_='2023')
        urls, nums = get_most_emoji(emoji_msgs)
        download_images = []
        for url in urls:
            download_images.append(download_image(url))
        for message in messages:
            if message[2] != 47:
                continue
            wxid = message[12].wxid
            bimg_num += 1
            if wxid not in bimg_rank:
                bimg_rank[wxid] = 0
            bimg_rank[wxid] += 1

        # 画图
        background_image_path = './data/pic/wechat.png'
        background_image = Image.open(background_image_path)
        background_image = draw_text(background_image, f"『{year}年度·表情包』", 40, (320, 40), align="center", max_width=500)
        x = 60
        y = 100
        space = 10

        background_image, height = draw_multi_text(background_image, ["本群一共发送了", str(bimg_num), "张表情包"], [30,55,30],(x,y),
                                        color_list=["white", "#fbb5cd", "white"],font_width_list=["normal", "bold", "normal"],
                                        space=[5,5,0],
                                        top_margin=[0,0,0])
        y += height+space+20
        for i in range(2):
            for j in range(6):
                idx = i*6+j
                background_image = insert_image(background_image, download_images[idx], (20+100*j, y+i*100), (100, 100))
        y += 200 + space + 30
        background_image = get_rank_list(background_image, (50,y), 600, bimg_rank, contacts, unit="张", limit=min(7, len(bimg_rank)), tag="表情包排行")

        background_image.save(output_path)
        print("生成完成，路径在：", f"生成结果 {output_path}")
    
    # def page_revoke():
        
    # page_one()
    page_two()
    # page_three()
    # page_img()
    # try:
        # first_message, first_time = msg_db.get_first_time_of_message(contact.wxid)
    # except TypeError:
    #     first_time = '2023-01-01 00:00:00'
    # data = {
    #     'ta_avatar_path': contact.avatar_path,
    #     'my_avatar_path': Me().avatar_path,
    #     'ta_nickname': contact.remark,
    #     'my_nickname': Me().name,
    #     'first_time': first_time,
    # }
    # wordcloud_cloud_data = analysis.wordcloud_christmas(contact.wxid)
    # msg_data = msg_db.get_messages_by_hour(contact.wxid, year_="2023")
    # msg_data.sort(key=lambda x: x[1], reverse=True)
    # desc = {
    #     '夜猫子': {'22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00'},
    #     '正常作息': {'06:00', "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00",
    #                  "17:00", "18:00", "19:00", "20:00", "21:00"},
    # }
    # time_, num = msg_data[0] if msg_data else ('', 0)
    # chat_time = f"凌晨{time_}" if time_ in {'00:00', '01:00', '02:00', '03:00', '04:00'``, '05:00'} else time_
    # label = '夜猫子'
    # for key, item in desc.items():
    #     if time_ in item:
    #         label = key
    # latest_dialog = msg_db.get_latest_time_of_message(contact.wxid, year_='2023')
    # latest_time = latest_dialog[0][2] if latest_dialog else ''
    # time_data = {
    #     'latest_time': latest_time,
    #     'latest_time_dialog': latest_dialog,
    #     'chat_time_label': label,
    #     'chat_time': chat_time,
    #     'chat_time_num': num,
    # }
    # month_data = msg_db.get_messages_by_month(contact.wxid, True, year_='2023')

    # if month_data:
    #     month_data.sort(key=lambda x: x[1])
    #     max_month, max_num = month_data[-1]
    #     min_month, min_num = month_data[0]
    #     min_month = min_month[-2:].lstrip('0') + '月'
    #     max_month = max_month[-2:].lstrip('0') + '月'
    # else:
    #     max_month, max_num = '月份', 0
    #     min_month, min_num = '月份', 0
    # month_data = {
    #     'year': '2023',
    #     'total_msg_num': msg_db.get_messages_number(contact.wxid, '2023'),
    #     'max_month': max_month,
    #     'min_month': min_month,
    #     'max_month_num': max_num,
    #     'min_month_num': min_num,
    # }
    # calendar_data = analysis.calendar_chart(contact.wxid, True, year='2023')
    # emoji_msgs = msg_db.get_messages_by_type(contact.wxid, 47, year_='2023', isSender_=0)
    # url, num = get_most_emoji(emoji_msgs)
    # me_emoji_msgs = msg_db.get_messages_by_type(contact.wxid, 47, year_='2023', isSender_=1)
    # me_url, me_num = get_most_emoji(me_emoji_msgs)
    # emoji_data = {
    #     'emoji_total_num': len(emoji_msgs),
    #     'emoji_url_num': zip(url, num),
    #     'me_emoji_total_num': len(me_emoji_msgs),
    #     'me_emoji_url_num': zip(me_url, me_num),
    # }
    # return render_template("christmas.html", **data, **wordcloud_cloud_data, **time_data, **month_data, **calendar_data,
    #                        **emoji_data)

@app.route("/christmas")
def christmas():
    # 渲染模板，并传递图表的 HTML 到模板中
    try:
        first_message, first_time = msg_db.get_first_time_of_message(contact.wxid)
    except TypeError:
        first_time = '2023-01-01 00:00:00'
    data = {
        'ta_avatar_path': contact.avatar_path,
        'my_avatar_path': Me().avatar_path,
        'ta_nickname': contact.remark,
        'my_nickname': Me().name,
        'first_time': first_time,
    }
    wordcloud_cloud_data = analysis.wordcloud_christmas(contact.wxid)
    msg_data = msg_db.get_messages_by_hour(contact.wxid, year_="2023")
    msg_data.sort(key=lambda x: x[1], reverse=True)
    desc = {
        '夜猫子': {'22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00'},
        '正常作息': {'06:00', "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00",
                     "17:00", "18:00", "19:00", "20:00", "21:00"},
    }
    time_, num = msg_data[0] if msg_data else ('', 0)
    chat_time = f"凌晨{time_}" if time_ in {'00:00', '01:00', '02:00', '03:00', '04:00', '05:00'} else time_
    label = '夜猫子'
    for key, item in desc.items():
        if time_ in item:
            label = key
    latest_dialog = msg_db.get_latest_time_of_message(contact.wxid, year_='2023')
    latest_time = latest_dialog[0][2] if latest_dialog else ''
    time_data = {
        'latest_time': latest_time,
        'latest_time_dialog': latest_dialog,
        'chat_time_label': label,
        'chat_time': chat_time,
        'chat_time_num': num,
    }
    month_data = msg_db.get_messages_by_month(contact.wxid, True, year_='2023')

    if month_data:
        month_data.sort(key=lambda x: x[1])
        max_month, max_num = month_data[-1]
        min_month, min_num = month_data[0]
        min_month = min_month[-2:].lstrip('0') + '月'
        max_month = max_month[-2:].lstrip('0') + '月'
    else:
        max_month, max_num = '月份', 0
        min_month, min_num = '月份', 0
    month_data = {
        'year': '2023',
        'total_msg_num': msg_db.get_messages_number(contact.wxid, '2023'),
        'max_month': max_month,
        'min_month': min_month,
        'max_month_num': max_num,
        'min_month_num': min_num,
    }
    calendar_data = analysis.calendar_chart(contact.wxid, True, year='2023')
    emoji_msgs = msg_db.get_messages_by_type(contact.wxid, 47, year_='2023', isSender_=0)
    url, num = get_most_emoji(emoji_msgs)
    me_emoji_msgs = msg_db.get_messages_by_type(contact.wxid, 47, year_='2023', isSender_=1)
    me_url, me_num = get_most_emoji(me_emoji_msgs)
    emoji_data = {
        'emoji_total_num': len(emoji_msgs),
        'emoji_url_num': zip(url, num),
        'me_emoji_total_num': len(me_emoji_msgs),
        'me_emoji_url_num': zip(me_url, me_num),
    }
    return render_template("christmas.html", **data, **wordcloud_cloud_data, **time_data, **month_data, **calendar_data,
                           **emoji_data)

@app.route('/home')
def home():
    try:
        first_message, first_time = msg_db.get_first_time_of_message(contact.wxid)
    except TypeError:
        return set_text('咱就是说，一次都没聊过就别分析了')
    data = {
        'sub_title': '二零二三年度报告',
        'avatar_path': contact.avatar_path,
        'nickname': contact.remark,
        'first_time': first_time,
    }

    return render_template('home.html', **data)


@app.route('/wordcloud/<who>/')
def one(who):
    wxid = contact.wxid
    # wxid = 'wxid_lltzaezg38so22'
    # print('wxid:'+wxid)
    world_cloud_data = analysis.wordcloud(wxid, who=who)  # 获取与Ta的对话数据
    # print(world_cloud_data)
    who = "你" if who == '1' else "TA"
    with open('wordcloud.html', 'w', encoding='utf-8') as f:
        f.write(render_template('wordcloud.html', **world_cloud_data))
    return render_template('wordcloud.html', **world_cloud_data, who=who)


def set_text(text):
    html = '''
        <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Centered Text</title>
        <style>
            body {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }

            .centered-text {
                font-size: 2em;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="centered-text">
            <!-- 这里是要显示的四个大字 -->
            %s
            <img src="https://res.wx.qq.com/t/wx_fed/we-emoji/res/v1.2.8/assets/newemoji/Yellowdog.png" id="旺柴" class="emoji_img">
        </div>
    </body>
    </html>
        ''' % (text)
    return html


@app.route('/test')
def test():
    return set_text('以下内容仅对VIP开放')


def run(port=21314):
    if contacts is not None:
        christmasForRoom()
    else:
        app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


@app.route('/data/avatar/<filename>')
def get_image(filename):
    try:
        # 返回动态生成的图片
        return send_file(os.path.join("../../data/avatar/", filename), mimetype='image/png')
    except:
        return send_file(os.path.join(f"{os.getcwd()}/data/avatar/", filename), mimetype='image/png')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
