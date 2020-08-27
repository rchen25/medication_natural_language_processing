import datetime


def parse_date(dateString):
    if "T" in dateString:
        return datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%S.%f0")
    if "-" in dateString:
        return datetime.datetime.strptime(dateString, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(dateString, "%Y%m%d")


def parse_rx_string(txt):
    suppClass = str(txt)
    if txt.find("("):
        suppClass = txt[txt.rfind("(") + 1:txt.find(")")]
        txt = txt[:txt.find("(")].strip()
    return txt, suppClass


def set_to_list(sDict):
    return dict(map(lambda (k, v): (k, list(v)), sDict.iteritems()))


def get_li_a_text(soup_li, toLower=True):
    aItem = soup_li.find('a')
    if aItem is None:
        return None
    txt = aItem.getText() + ' '
    if txt == ' ':
        return None
    txtAscii = txt.encode('ascii', 'ignore').strip()
    if toLower:
        txtAscii = txtAscii.lower()
    return txtAscii


def parse_li_item(soup_li):
    """
    Parse the hyper link in a file by converting it to ascii
    The pattern is drug name (drug category)
    """
    txt = get_li_a_text(soup_li)
    if txt is None:
        return None, None
    txt, suppClass = parse_rx_string(txt)
    if suppClass == '':
        return None, None
    return txt, suppClass


def not_decimal(x):
    """
    Return true if it's not a decimal
    """
    try:
        float(x)
    except ValueError:
        return True
    else:
        return False


def clean_words(words):
    words = map(lambda x: x.strip(), words)
    words = filter(not_decimal, words)
    words = filter(None, words)
    return words


def format_txt(word):
    return word.lower().strip()
