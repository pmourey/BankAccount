#
#   Programme d'analyse des relevés PDF bancaires
#
# REf tutorial YouTube: https://www.youtube.com/watch?v=w2r2Bg42UPY
#
import locale
import mimetypes
import os
import re
from dataclasses import dataclass
from enum import Enum

from pdfminer.high_level import extract_pages, extract_text
import tabula
from datetime import datetime


class ACType(Enum):
    CCP = 0
    LIVRET_A = 1
    CSL = 2
    LDD = 3


@dataclass
class Account:
    type: ACType
    ref: str


@dataclass
class Statement:
    account: Account
    date: datetime
    value: float
    num: int


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Définir la localisation en français
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    accounts = [Account(ACType.CCP, 'XX XXX XX Y XXX'),
                Account(ACType.LIVRET_A, 'XXX XXXXXXX Y'),
                Account(ACType.CSL, 'XXX XXXXXXX Y'),
                Account(ACType.LDD, 'XXX XXXXXXX Y')]
    statements = []
    processed_statements = []
    directory_path = os.getcwd() + '/Relevés bancaires/'
    print(directory_path)
    with os.scandir(directory_path) as entries:
        for entry in entries:
            extension = os.path.splitext(entry)[1]
            type_mime, _ = mimetypes.guess_type(entry)
            if entry.is_file() and type_mime == 'application/pdf':
                # print(f"PDF File: {entry.name}")
                # tables = tabula.read_pdf(entry)
                # print(tables)
                # for page_layout in extract_pages(directory_path + entry.name):
                #     for element in page_layout:
                #         print(element)
                text = extract_text(directory_path + entry.name)
                start_parsing = False
                account_no = 0
                for line in text.split('\n'):
                    if 'RelevØ de vos comptes' in line:
                        statement_num: int = int(line.split('-')[1].split()[1])
                    elif 'Situation de vos comptes' in line:
                        # print(line)
                        date_str = ' '.join(line.split()[5:]).replace('Ø', 'é').replace('ß', 'û')
                        format_str = "%d %B %Y"
                        date_obj = datetime.strptime(date_str, format_str)
                        if (statement_num, date_obj) in processed_statements:
                            break
                        processed_statements.append((statement_num, date_obj))
                        # print(date_obj)
                        start_parsing = True
                    elif start_parsing:
                        if 'cid:128' in line and account_no < len(accounts):
                            solde = line.split('(')[0]
                            account = accounts[account_no]
                            value: str = solde.replace(',', '.').replace(' ', '')
                            statements.append(Statement(account, date_obj, float(value), statement_num))
                            # print(solde)
                            account_no += 1
                # pattern = re.compile(r"Livret A")
                # matches = pattern.findall(text)
                # print(matches)
            elif entry.is_dir():
                print(f"Directory: {entry.name}")

    # Affichage des soldes totaux de chaque relevé
    dates = list(set([s.date for s in statements]))
    dates.sort()
    for date in dates:
        solde = sum([s.value for s in statements for a in accounts if s.account == a and s.date == date])
        statement_num: int = list(set([s.num for s in statements if s.date == date]))[0]
        date_str = date.strftime("%d %B %Y")
        print(f'Relevé n°{statement_num} du {date_str:<20s}: {round(solde, 2)}')

