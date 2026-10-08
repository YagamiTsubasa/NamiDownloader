import os
import signal
import sys
from pathlib import Path
from PySide6.QtCore import QProcess, QTimer, QUrl, QSettings
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPlainTextEdit, QLineEdit, QPushButton, QFileDialog,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from core import command, extract_urls, platform_for, tools_dir, friendly_error, redact

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('纳米素材下载器 · 0.1 测试版')
        self.resize(960, 730)
        self.settings = QSettings('Nami', 'Downloader')
        self.jobs = []
        self.active = None
        self.proc = None
        self.stopped = False
        self.buffer = ''
        base = QWidget(); self.setCentralWidget(base)
        layout = QVBoxLayout(base); layout.setContentsMargins(24, 20, 24, 20); layout.setSpacing(12)
        title = QLabel('纳米素材下载器'); title.setStyleSheet('font-size:25px;font-weight:700')
        layout.addWidget(title)
        layout.addWidget(QLabel('YouTube / B站  ·  本地保存  ·  抖音、TikTok、小红书待接入'))
        self.links = QPlainTextEdit(); self.links.setPlaceholderText('粘贴视频链接，一行一个；也可以粘贴带链接的分享文案。\n第一版按单个视频处理，不批量下载整个频道或播放列表。')
        self.links.setMaximumHeight(120); layout.addWidget(self.links)
        row = QHBoxLayout(); self.dest = QLineEdit(str(self.settings.value('directory', str(Path.home() / 'Downloads' / 'Nami'))))
        pick = QPushButton('选择目录'); pick.clicked.connect(self.pick)
        row.addWidget(QLabel('保存到')); row.addWidget(self.dest); row.addWidget(pick); layout.addLayout(row)
        row = QHBoxLayout()
        self.quality = QComboBox(); self.quality.addItems(['1080', '720', '2160'])
        self.number = QSpinBox(); self.number.setRange(1, 999999); self.number.setValue(1)
        self.browser = QComboBox(); self.browser.addItem('不读取登录状态', ''); self.browser.addItem('Chrome（需授权）', 'chrome'); self.browser.addItem('Firefox（需授权）', 'firefox')
        for label, widget in [('最高画质', self.quality), ('起始编号', self.number), ('登录状态', self.browser)]:
            row.addWidget(QLabel(label)); row.addWidget(widget)
        layout.addLayout(row)
        self.proxy = QLineEdit(); self.proxy.setPlaceholderText('可选代理，例如 http://127.0.0.1:7890；留空使用下载引擎默认网络设置')
        layout.addWidget(self.proxy)
        row = QHBoxLayout()
        self.start_btn = QPushButton('开始下载'); self.start_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton('停止队列'); self.stop_btn.clicked.connect(self.stop); self.stop_btn.setEnabled(False)
        self.retry_btn = QPushButton('重试失败 / 已停止'); self.retry_btn.clicked.connect(self.retry)
        folder = QPushButton('打开保存目录'); folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.dest.text())))
        for b in [self.start_btn, self.stop_btn, self.retry_btn, folder]: row.addWidget(b)
        layout.addLayout(row)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(['编号', '平台', '链接', '状态'])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 220); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.details); layout.addWidget(self.table)
        self.detail = QPlainTextEdit(); self.detail.setReadOnly(True); self.detail.setMaximumHeight(100)
        self.detail.setPlaceholderText('选中任务查看详情。登录信息不会写入日志。'); layout.addWidget(self.detail)
        self.status = QLabel('准备就绪 · MP4 封装不保证 H.264 编码；第一版保留下载源编码。'); layout.addWidget(self.status)

    def pick(self):
        result = QFileDialog.getExistingDirectory(self, '选择保存目录', self.dest.text())
        if result: self.dest.setText(result)

    def lock(self, busy):
        for w in [self.start_btn, self.retry_btn, self.dest, self.quality, self.number, self.browser, self.proxy, self.links]: w.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)

    def start(self):
        urls = extract_urls(self.links.toPlainText())
        if not urls:
            QMessageBox.information(self, '缺少链接', '请粘贴至少一个视频链接。'); return
        missing = [x for x in ('yt-dlp', 'ffmpeg', 'ffprobe', 'deno') if not os.access(tools_dir() / x, os.X_OK)]
        if missing:
            QMessageBox.warning(self, '应用组件不完整', '缺少：' + ', '.join(missing) + '\n请让打包者重新构建完整应用，同事无需安装依赖。'); return
        if self.browser.currentData():
            answer = QMessageBox.question(self, '授权读取登录状态', '本次任务将读取所选浏览器的 Cookie，用于访问对应网站，可能触发钥匙串授权。\n不发送到第三方解析服务，不记录到日志。是否继续？')
            if answer != QMessageBox.Yes: return
        try:
            directory = Path(self.dest.text()).expanduser().resolve(); directory.mkdir(parents=True, exist_ok=True)
            import tempfile
            with tempfile.TemporaryFile(dir=directory): pass
            command('https://youtu.be/validation', directory, self.number.value(), self.quality.currentText(), self.browser.currentData(), self.proxy.text().strip())
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, '无法开始', str(e)); return
        self.settings.setValue('directory', str(directory))
        self.jobs = []; self.table.setRowCount(0)
        for i, url in enumerate(urls):
            job = dict(url=url, number=self.number.value()+i, state='待下载', detail='', output=directory,
                       quality=self.quality.currentText(), browser=self.browser.currentData(), proxy=self.proxy.text().strip())
            try: job['platform'] = platform_for(url).name
            except ValueError as e: job.update(platform='未接入', state='不支持', detail=str(e))
            self.jobs.append(job); self.table.insertRow(i)
            for col, val in enumerate([job['number'], job['platform'], url, job['state']]): self.table.setItem(i, col, QTableWidgetItem(str(val)))
        self.stopped = False; self.lock(True); self.next_job()

    def update_job(self, index, state):
        self.jobs[index]['state'] = state; self.table.item(index, 3).setText(state)

    def next_job(self):
        pending = next((i for i,j in enumerate(self.jobs) if j['state'] == '待下载'), None)
        if self.stopped or pending is None:
            self.active = None; self.lock(False)
            completed = sum(j['state']=='完成' for j in self.jobs)
            self.status.setText(f'队列结束：完成 {completed} / {len(self.jobs)}；可重试失败任务。'); return
        self.active = pending; job = self.jobs[pending]; self.buffer = ''; job['detail'] = ''; job['file'] = ''
        self.update_job(pending, '正在解析…')
        self.proc = QProcess(self); self.proc.setProcessChannelMode(QProcess.MergedChannels)
        if sys.platform != 'win32':
            params = QProcess.UnixProcessParameters()
            params.flags = QProcess.UnixProcessFlag.CreateNewSession
            self.proc.setUnixProcessParameters(params)
        self.proc.readyReadStandardOutput.connect(self.read_output)
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(self.process_error)
        args = command(job['url'], job['output'], job['number'], job['quality'], job['browser'], job['proxy'])
        self.proc.start(args[0], args[1:])

    def process_error(self, error):
        if error == QProcess.FailedToStart and self.active is not None:
            self.jobs[self.active]['detail'] = '下载引擎无法启动，请检查构建包与当前 macOS 的兼容性。'
            self.finished(-1, QProcess.CrashExit)

    def read_output(self):
        if not self.proc: return
        self.buffer += bytes(self.proc.readAllStandardOutput()).decode('utf-8', errors='replace')
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1); self.consume(line.strip())

    def consume(self, line):
        if self.active is None: return
        job = self.jobs[self.active]
        if line.startswith('NAMI_PROGRESS:'):
            self.update_job(self.active, '下载 ' + line.split(':', 1)[1].strip())
        elif line.startswith('NAMI_FILE:'):
            job['file'] = line.split(':', 1)[1]
        elif line:
            job['detail'] = (job['detail'] + '\n' + redact(line))[-6000:]
            if '[Merger]' in line or '[VideoRemuxer]' in line: self.update_job(self.active, '合并 / 整理文件…')
        self.details()

    def finished(self, code, exit_status):
        if self.active is None: return
        self.read_output()
        if self.buffer: self.consume(self.buffer); self.buffer = ''
        job = self.jobs[self.active]
        success = code == 0 and job.get('file') and Path(job['file']).is_file()
        state = '已停止' if self.stopped else ('完成' if success else '失败')
        if state == '失败': job['detail'] = friendly_error(job['detail']) + '\n' + job['detail']
        if success: job['detail'] = '已保存：' + job['file']
        self.update_job(self.active, state); self.details()
        old = self.proc; self.proc = None; self.active = None
        if old: old.deleteLater()
        QTimer.singleShot(0, self.next_job)

    def stop(self):
        self.stopped = True
        for i, j in enumerate(self.jobs):
            if j['state'] == '待下载': self.update_job(i, '已停止')
        if self.proc:
            process = self.proc
            pid = process.processId()
            try:
                if pid and sys.platform != 'win32': os.killpg(pid, signal.SIGTERM)
                else: process.terminate()
            except ProcessLookupError: pass
            # Kill only this process, never a subsequent retry process.
            def kill_if_running():
                try:
                    if process.state() != QProcess.NotRunning:
                        if pid and sys.platform != 'win32':
                            try: os.killpg(pid, signal.SIGKILL)
                            except ProcessLookupError: pass
                        else: process.kill()
                except RuntimeError: pass
            QTimer.singleShot(3000, kill_if_running)

    def retry(self):
        for i, job in enumerate(self.jobs):
            if job['state'] in ('失败', '已停止'): self.update_job(i, '待下载')
        if self.jobs: self.stopped = False; self.lock(True); self.next_job()

    def details(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.jobs): self.detail.setPlainText(self.jobs[row]['detail'])

    def closeEvent(self, event):
        if self.proc and self.proc.state() != QProcess.NotRunning:
            QMessageBox.information(self, '任务进行中', '请先停止队列，等待停止后再关闭窗口。'); event.ignore()
        else: event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv); app.setStyle('Fusion')
    app.setWindowIcon(QIcon(str(Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets' / 'icon.png')))
    window = Window(); window.show(); sys.exit(app.exec())
