import requests
import os
import re
import time
from base64 import standard_b64encode
from .exceptions import UnknownConnectionError
from .myutil import checkpath
from youtube_transcript_api import VideoUnavailable

fmt_headers = ['start', 'duration', 'text']

HEADER_HTML = '''
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
'''

TABLE_CSS = '''
table.css {
 border-collapse: collapse;
}
 
table.css thead{
 border-collapse: collapse;
 border: 1px solid #000
}
 
table.css tr td{
 padding: 0.3em;
 border: 1px solid #000
}

table.css th{
 padding: 0.3em;
 border: 1px solid #000
}
'''


class HTMLArchiver:
    '''
    HTMLArchiver saves transcript data as HTML table format.
    '''
    def __init__(self, save_path, callback=None):
        super().__init__()
        self.save_path = checkpath(save_path)
        self.header = [HEADER_HTML]
        self.body = ['<body>\n', '<table class="css">\n', self._parse_table_header(fmt_headers)]
        self.callback = callback


    def process(self, transcripts: list):
        """
        Returns
        ----------
        dict :
            save_path : str :
                Actual save path of file.
            total_lines : int :
                count of total lines written to the file.
        """
        if transcripts is None or len(transcripts) == 0:
            return
        for c in transcripts:
            try:
                self.body.append(
                    self._parse_html_line((
                        self.duration_convert(c.start),
                        '<div align="right">' + str(round(c.duration, 2)) + '</div>' ,
                        c.text
                    )
                ))
                if self.callback:
                    self.callback(None, 1)
            except AttributeError as exc:
                if c.get("error"):
                    raise AttributeError from exc
            

    def _parse_html_line(self, raw_line):
        return ''.join(('<tr>',
                        ''.join(''.join(('<td>', cell, '</td>')) for cell in raw_line),
                        '</tr>\n'))

    def _parse_table_header(self, raw_line):
        return ''.join(('<thead><tr>',
                        ''.join(''.join(('<th>', cell, '</th>')) for cell in raw_line),
                        '</tr></thead>\n'))


    def _create_styles(self):
        return '\n'.join(('<style type="text/css">',
                          TABLE_CSS,
                          '</style>\n'))
    
    def finalize(self):
        self.header.extend([self._create_styles(), '</head>\n'])
        self.body.extend(['</table>\n</body>\n</html>'])
        with open(self.save_path, mode='a', encoding='utf-8') as f:
            f.writelines(self.header)
            f.writelines(self.body)

    def duration_convert(self, duration):
        d = round(duration)
        ret = []
        for i in range(3):
            ret.append(str(d%60).zfill(2))
            d//=60
        return ":".join(reversed(ret))

    