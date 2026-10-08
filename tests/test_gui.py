import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QProcess, QSettings
import app as gui

MOCK = '''#!/usr/bin/env python3
import sys, time
from pathlib import Path
args = sys.argv[1:]
url = args[-1]
if 'slow' in url:
    print('NAMI_PROGRESS:10%', flush=True)
    time.sleep(20)
if 'fail' in url:
    print('ERROR: HTTP Error 403 Forbidden', flush=True)
    sys.exit(1)
out = Path(args[args.index('--paths')+1]) / args[args.index('--output')+1].replace('%(id)s', 'test').replace('%(ext)s','mp4')
out.write_bytes(b'FAKE_VIDEO_TEST_ONLY')
print('NAMI_PROGRESS:100%', flush=True)
print('NAMI_FILE:' + str(out), flush=True)
'''

class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ('yt-dlp','ffmpeg','ffprobe','deno'):
            file = self.root / name; file.write_text(MOCK); file.chmod(0o755)
        self.p1 = patch('core.tools_dir', return_value=self.root); self.p1.start()
        self.p2 = patch('app.tools_dir', return_value=self.root); self.p2.start()
        self.p3 = patch('app.QSettings', return_value=QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat)); self.p3.start()
        self.window = gui.Window(); self.window.dest.setText(str(self.root))
    def tearDown(self):
        self.window.close(); self.p1.stop(); self.p2.stop(); self.p3.stop(); self.tmp.cleanup()
    def wait(self, predicate, timeout=5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.qt.processEvents()
            if predicate(): return
            time.sleep(.01)
        self.fail('Timed out waiting for process/queue')
    def test_mixed_batch_retry(self):
        self.window.links.setPlainText('https://v.douyin.com/a\nhttps://youtu.be/good\nhttps://b23.tv/fail')
        self.window.start()
        self.wait(lambda: self.window.start_btn.isEnabled())
        self.assertEqual([j['state'] for j in self.window.jobs], ['不支持','完成','失败'])
        self.assertIn('平台拒绝', self.window.jobs[2]['detail'])
        self.window.jobs[2]['url'] = 'https://b23.tv/good'
        self.window.retry(); self.wait(lambda: self.window.start_btn.isEnabled())
        self.assertEqual(self.window.jobs[2]['state'], '完成')
        self.assertEqual(self.window.jobs[2]['number'], 3)
    def test_cancel_queue(self):
        self.window.links.setPlainText('https://youtu.be/slow\nhttps://youtu.be/next')
        self.window.start()
        self.wait(lambda: self.window.proc is not None and self.window.proc.state() == QProcess.Running)
        self.window.stop(); self.wait(lambda: self.window.start_btn.isEnabled())
        self.assertEqual([j['state'] for j in self.window.jobs], ['已停止','已停止'])

if __name__ == '__main__': unittest.main()
