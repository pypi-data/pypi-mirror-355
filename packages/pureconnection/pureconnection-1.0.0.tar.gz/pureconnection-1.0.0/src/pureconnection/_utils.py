# src/proyekku/printer.py

import json
from pprint import pprint

class PrettyPrinter:
    def __init__(self, style="json"):
        """
        Inisialisasi pretty printer.
        style: 'json' atau 'pprint'
        """
        self.style = style

    def print(self, data):
        """
        Cetak data dengan gaya yang dipilih.
        """
        if self.style == "json":
            print(json.dumps(data, indent=4, ensure_ascii=False))
        elif self.style == "pprint":
            pprint(data, indent=4)
        else:
            print(data)
