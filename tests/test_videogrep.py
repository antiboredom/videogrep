import os
import unittest
import videogrep

class TestVideogrep(unittest.TestCase):
    def test_convert_timestamp(self):
        self.assertEqual(videogrep.convert_timestamp('00:00:01,0'), 1.0)

    def test_srt_parse(self):
        pass

    def test_vtt_parse(self):
        pass

    def test_pocketsphinx_parse(self):
        pass

    def test_re_search(self):
        pass

    def test_hyper_search(self):
        pass

    def test_pos_search(self):
        pass

    def test_ngrams(self):
        pass

    def test_compose(self):
        pass

    def test_edl(self):
        pass

    def test_auto_source(self):
        pass

    def test_padding(self):
        pass

    def test_transcribe(self):
        pass

    def test_cli(self):
        pass

    def test_cleanup(self):
        pass

if __name__ == '__main__':
    unittest.main()
