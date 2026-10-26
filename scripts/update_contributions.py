"""Render the public GitHub contribution calendar as a local SVG."""
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = []
        self.heading = []
        self.in_heading = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h2' and attrs.get('id') == 'js-contribution-activity-description':
            self.in_heading = True
        if tag == 'td' and 'data-date' in attrs:
            self.days.append((date.fromisoformat(attrs['data-date']), int(attrs['data-level'])))

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)


def render(source):
    parser = CalendarParser()
    parser.feed(source)
    heading = ' '.join(' '.join(parser.heading).split())
    days = sorted(parser.days)
    if len(days) < 350 or 'contributions in the last year' not in heading:
        raise ValueError('GitHub returned an incomplete calendar; keeping the existing SVG.')
    colors = ['#18252D', '#304C3B', '#52744E', '#7FA873', '#A8C99B']
    first = days[0][0]
    offset = (first.weekday() + 1) % 7
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="230" viewBox="0 0 960 230" role="img" aria-labelledby="title">',
        f'<title id="title">{escape(heading)}</title>',
        '<rect x="1" y="1" width="958" height="228" rx="12" fill="#0B1219" stroke="#2A3E49"/>',
        f'<text x="28" y="35" fill="#EDF2EB" font-family="Arial,sans-serif" font-size="19">{escape(heading)}</text>',
    ]
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for day, level in days:
        week = ((day - first).days + offset) // 7
        weekday = (day.weekday() + 1) % 7
        x, y = 64 + week * 16, 78 + weekday * 16
        if day.day == 1:
            parts.append(f'<text x="{x}" y="66" fill="#A9B8C4" font-family="Arial,sans-serif" font-size="11">{months[day.month - 1]}</text>')
        parts.append(f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" fill="{colors[level]}"><title>{day.isoformat()} · level {level}</title></rect>')
    for label, row in [('Mon', 1), ('Wed', 3), ('Fri', 5)]:
        parts.append(f'<text x="28" y="{88 + row * 16}" fill="#A9B8C4" font-family="Arial,sans-serif" font-size="10">{label}</text>')
    parts.append(f'<text x="28" y="209" fill="#A9B8C4" font-family="Arial,sans-serif" font-size="11">GitHub · {first.isoformat()} — {days[-1][0].isoformat()}</text>')
    parts.append('<text x="766" y="209" fill="#A9B8C4" font-family="Arial,sans-serif" font-size="11">Less</text>')
    for i, color in enumerate(colors):
        parts.append(f'<rect x="{798 + i * 16}" y="199" width="12" height="12" rx="2" fill="{color}"/>')
    parts.append('<text x="884" y="209" fill="#A9B8C4" font-family="Arial,sans-serif" font-size="11">More</text></svg>')
    (ROOT / 'src/profile/contributions.svg').write_text('\n'.join(parts), encoding='utf-8')
    print(f'{heading}; {len(days)} days rendered.')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        source = Path(sys.argv[1]).read_text(encoding='utf-8')
    else:
        request = Request('https://github.com/users/KauaRios/contributions', headers={'User-Agent': 'KauaRios-profile'})
        with urlopen(request, timeout=30) as response:
            source = response.read().decode('utf-8')
    render(source)
