import time
from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QDialog, QVBoxLayout, QCheckBox, QHBoxLayout, \
    QProgressBar, QLabel, QMessageBox

from app.DataBase import micro_msg_db, misc_db
from app.DataBase.output_pc import Output
from app.components import ScrollBar
from app.components.export_contact_item import ContactQListWidgetItem
from app.person import Contact
from app.ui.menu.exportUi import Ui_Dialog

types = {
    '文本': 1,
    '图片': 3,
    '语音': 34,
    '视频': 43,
    '表情包': 47,
    '音乐与音频': 4903,
    '文件': 4906,
    '分享卡片': 4905,
    '拍一拍等系统消息': 10000
}
file_format = {
    'Docx': Output.DOCX,
    'TXT': Output.TXT,
    'HTML': Output.HTML,
    'CSV': Output.CSV,
}
Stylesheet = """
QPushButton{
    background-color: #ffffff;
}
QPushButton:hover { 
    background-color: lightgray;
}
"""


class ExportDialog(QDialog, Ui_Dialog):
    def __init__(self, contact=None, title="选择导出的类型", file_type="html", parent=None):
        super(ExportDialog, self).__init__(parent)
        self.setupUi(self)
        self.contacts: List[Contact] = []
        self.setStyleSheet(Stylesheet)
        self.contact = contact
        self.btn_select_all.clicked.connect(self.select_all)
        self.select_all_flag = False
        self.btn_start.clicked.connect(self.export_data)
        self.comboBox_time.activated.connect(self.set_export_date)
        self.export_choices = {"文本": True, "图片": True, "语音": False, "视频": False, "表情包": False,
                               '音乐与音频': False, '分享卡片': False, '文件': False,
                               '拍一拍等系统消息': True}  # 定义导出的数据类型，默认全部选择
        self.setWindowTitle(title)
        self.resize(800, 600)
        self.worker = None  # 导出线程
        for export_type, default_state in self.export_choices.items():
            checkbox = QCheckBox(export_type)
            checkbox.setObjectName('message_type')
            checkbox.setChecked(default_state)
            self.verticalLayout_2.addWidget(checkbox)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.timer = QTimer(self)
        self.time = 0
        self.total_msg_num = 99999  # 总的消息个数
        self.num = 0  # 当前完成的消息个数
        self.timer.timeout.connect(self.update_elapsed_time)
        self.show_thread = ShowContactThread()
        self.show_thread.showSingal.connect(self.show_contact)
        # self.show_thread.load_finish_signal.connect(self.stop_loading)
        self.show_thread.start()
        self.listWidget.setVerticalScrollBar(ScrollBar())
        # self.listWidget.currentRowChanged.connect(self.setCurrentIndex)
        self.listWidget.itemClicked.connect(self.setCurrentIndex)
        self.visited = set()
        self.now_index = 0

    def set_export_date(self):
        date_range = self.comboBox_time.currentText()
        if date_range == '全部时间':
            pass
        elif date_range == '最近三个月':
            QMessageBox.warning(self,
                                "别急别急",
                                "马上就实现该功能"
                                )
        elif date_range == '自定义时间':
            QMessageBox.warning(self,
                                "别急别急",
                                "马上就实现该功能"
                                )

    def export_data(self):
        self.btn_start.setEnabled(False)
        # 在这里获取用户选择的导出数据类型
        selected_types = {types[export_type]: checkbox.isChecked() for export_type, checkbox in
                          zip(self.export_choices.keys(), self.findChildren(QCheckBox, 'message_type'))}

        # 在这里根据用户选择的数据类型执行导出操作
        print("选择的数据类型:", selected_types)

        file_types = []
        for checkbox in [self.checkBox_txt, self.checkBox_csv, self.checkBox_html, self.checkBox_word]:
            if checkbox.isChecked():
                file_types.append(file_format[checkbox.text()])
        select_contacts = []
        count = self.listWidget.count()
        # 遍历listwidget中的内容
        for i in range(count):
            item = self.listWidget.item(i)
            if item.is_select:
                select_contacts.append(self.contacts[i])
        # 在这里根据用户选择的数据类型执行导出操作
        print("选择的文件格式:", file_types)
        self.worker = Output(select_contacts, type_=Output.Batch, message_types=selected_types, sub_type=file_types)
        # self.worker.progressSignal.connect(self.update_progress)
        self.worker.okSignal.connect(self.export_finished)
        self.worker.rangeSignal.connect(self.set_total_msg_num)
        self.worker.nowContact.connect(self.update_progress)
        self.worker.start()
        # 启动定时器，每1000毫秒更新一次任务进度
        self.timer.start(1000)
        self.start_time = time.time()
        # self.accept()  # 使用accept关闭对话框
        # 绑定点击槽函数 点击显示对应item中的name

    def set_total_msg_num(self, num):
        self.total_msg_num = num
        # b''+num +(1,1)

    def setCurrentIndex(self, item):
        # print(row)
        # row = self.listWidget.it
        # item = self.listWidget.item(row)
        item.select()
        item.dis_select()
        # self.now_index = row

    def select_all(self):
        self.select_all_flag = not self.select_all_flag
        print('全选', self.select_all_flag)
        if self.select_all_flag:
            count = self.listWidget.count()
            # 遍历listwidget中的内容
            for i in range(count):
                item = self.listWidget.item(i)
                item.force_select()
            self.btn_select_all.setText('全不选')
        else:
            count = self.listWidget.count()
            # 遍历listwidget中的内容
            for i in range(count):
                item = self.listWidget.item(i)
                item.force_dis_select()
            self.btn_select_all.setText('全选')

    def export_finished(self):
        self.btn_start.setEnabled(True)
        self.time = 0
        end_time = time.time()
        print(f'总耗时:{end_time - self.start_time}s')
        reply = QMessageBox(self)
        reply.setIcon(QMessageBox.Information)
        reply.setWindowTitle('OK')
        reply.setText(f"导出聊天记录成功\n在./data/目录下(跟exe文件在一起)")
        reply.addButton("确认", QMessageBox.AcceptRole)
        reply.addButton("取消", QMessageBox.RejectRole)
        api = reply.exec_()
        self.accept()

    def show_contact(self, contact):
        # return
        # print(contact.remark)
        contact_item = ContactQListWidgetItem(contact.remark, contact.smallHeadImgUrl, contact.smallHeadImgBLOG)
        self.listWidget.addItem(contact_item)
        self.listWidget.setItemWidget(contact_item, contact_item.widget)
        self.contacts.append(contact)

    def update_elapsed_time(self):
        self.time += 1
        self.label_time.setText(f"耗时: {self.time}s")

    def update_progress(self, remark):
        self.num += 1
        progress_percentage = int((self.num) / self.total_msg_num * 100)
        self.progressBar.setValue(progress_percentage)
        self.label_process.setText(f"导出进度: {progress_percentage}% {remark}")


class ShowContactThread(QThread):
    showSingal = pyqtSignal(Contact)
    load_finish_signal = pyqtSignal(bool)

    # heightSingal = pyqtSignal(int)
    def __init__(self):
        super().__init__()

    def run(self) -> None:
        contact_info_lists = micro_msg_db.get_contact()
        for contact_info_list in contact_info_lists:
            # UserName, Alias,Type,Remark,NickName,PYInitial,RemarkPYInitial,ContactHeadImgUrl.smallHeadImgUrl,ContactHeadImgUrl,bigHeadImgUrl
            contact_info = {
                'UserName': contact_info_list[0],
                'Alias': contact_info_list[1],
                'Type': contact_info_list[2],
                'Remark': contact_info_list[3],
                'NickName': contact_info_list[4],
                'smallHeadImgUrl': contact_info_list[7]
            }
            contact = Contact(contact_info)
            contact.smallHeadImgBLOG = misc_db.get_avatar_buffer(contact.wxid)
            contact.set_avatar(contact.smallHeadImgBLOG)
            self.showSingal.emit(contact)
            # print(contact.wxid)
            # pprint(contact.__dict__)
        self.load_finish_signal.emit(True)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    dialog = ExportDialog()
    result = dialog.exec_()  # 使用exec_()获取用户的操作结果
    if result == QDialog.Accepted:
        print("用户点击了导出按钮")
    else:
        print("用户点击了取消按钮")
    sys.exit(app.exec_())
