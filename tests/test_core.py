import unittest
from pathlib import Path
from core import command, extract_urls, platform_for, redact

class CoreTests(unittest.TestCase):
    def test_host_boundary(self):
        for url in ['https://youtube.com.attacker.test/a', 'https://notyoutube.com/a', 'file:///a', 'https://user:pw@youtube.com/a']:
            with self.assertRaises(ValueError): platform_for(url)
        self.assertEqual(platform_for('https://m.youtube.com/watch?v=a').name, 'YouTube')
        self.assertEqual(platform_for('https://b23.tv/abcd').name, 'B站')
    def test_reserved_platforms(self):
        for url in ['https://v.douyin.com/a', 'https://www.tiktok.com/a', 'https://xhslink.com/a']:
            with self.assertRaisesRegex(ValueError, '尚未接入'): platform_for(url)
    def test_share_and_dedup(self):
        self.assertEqual(extract_urls('视频 https://b23.tv/abc。\nhttps://b23.tv/abc'), ['https://b23.tv/abc'])
    def test_shell_free_and_defaults(self):
        url = 'https://www.youtube.com/watch?v=abc&list=xyz'
        args = command(url, Path('/tmp/with spaces'), 96, '720')
        self.assertEqual(args[-2:], ['--', url])
        self.assertIn('--ignore-config', args)
        self.assertIn('--no-overwrites', args)
        self.assertNotIn('--cookies-from-browser', args)
        self.assertIn('0096_%(id)s.%(ext)s', args)
        self.assertIn('bv*[height<=720]+ba/b[height<=720]', args)
    def test_proxy(self):
        with self.assertRaises(ValueError): command('https://youtu.be/abc', '/tmp', 1, '1080', proxy='http://u:p@host')
    def test_redaction(self):
        msg = redact('ERROR https://site.test/?token=secret\nCookie: secret')
        self.assertNotIn('secret', msg)

if __name__ == '__main__': unittest.main()
