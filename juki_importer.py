from urllib.request import Request, urlopen
from html.parser import HTMLParser


URL = "https://www.juki.co.jp/industrial_e/products_e/apparel_e/1needle_lock_e/detail.php?cd=DDL-8700_E"


class TableParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.in_table = False
        self.in_row = False
        self.in_cell = False

        self.current_row = []
        self.current_cell = ""

        self.tables = []
        self.current_table = []

    def handle_starttag(self, tag, attrs):

        if tag == "table":
            self.in_table = True
            self.current_table = []

        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_row = []

        elif tag in ("th", "td") and self.in_row:
            self.in_cell = True
            self.current_cell = ""

    def handle_data(self, data):

        if self.in_cell:
            self.current_cell += data

    def handle_endtag(self, tag):

        if tag in ("th", "td") and self.in_cell:

            value = " ".join(self.current_cell.split())

            if value:
                self.current_row.append(value)

            self.in_cell = False

        elif tag == "tr" and self.in_row:

            if self.current_row:
                self.current_table.append(self.current_row)

            self.in_row = False

        elif tag == "table" and self.in_table:

            if self.current_table:
                self.tables.append(self.current_table)

            self.current_table = []
            self.in_table = False


def ambil_spesifikasi_ddl8700():

    request = Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=15) as response:

        html = response.read().decode(
            "utf-8",
            errors="ignore"
        )

    parser = TableParser()
    parser.feed(html)

    for table in parser.tables:

        if not table:
            continue

        if (
            len(table[0]) >= 2
            and table[0][1].strip() == "DDL-8700"
        ):

            data = []

            for row in table[1:]:

                if len(row) >= 2:

                    data.append(
                        (
                            row[0].strip(),
                            row[1].strip()
                        )
                    )

            return data

    raise ValueError(
        "Tabel DDL-8700 tidak ditemukan."
    )
