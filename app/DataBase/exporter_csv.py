import csv
import os

from app.DataBase import msg_db
from app.DataBase.output import ExporterBase
from app.DataBase.package_msg import PackageMsg


class CSVExporter(ExporterBase):
    def to_csv(self):
        origin_docx_path = f"{os.path.abspath('.')}/data/聊天记录/{self.contact.remark}"
        os.makedirs(origin_docx_path, exist_ok=True)
        filename = f"{os.path.abspath('.')}/data/聊天记录/{self.contact.remark}/{self.contact.remark}_utf8.csv"
        columns = ['localId', 'TalkerId', 'Type', 'SubType',
                   'IsSender', 'CreateTime', 'Status', 'StrContent',
                   'StrTime', 'Remark', 'NickName', 'Sender']
        if self.contact.is_chatroom:
            packagemsg = PackageMsg()
            messages = packagemsg.get_package_message_by_wxid(self.contact.wxid)
        else:
            messages = msg_db.get_messages(self.contact.wxid)
        # 写入CSV文件
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            # 写入数据
            # writer.writerows(messages)
            for msg in messages:
                other_data = [msg[12].remark, msg[12].nickName, msg[12].wxid] if self.contact.is_chatroom else []
                writer.writerow([*msg[:9], *other_data])
        self.okSignal.emit('ok')

    def run(self):
        self.to_csv()
