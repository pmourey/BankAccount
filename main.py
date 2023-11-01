#
#   Programme d'analyse des relevés PDF bancaires
#
# REf tutorial YouTube: https://www.youtube.com/watch?v=w2r2Bg42UPY
#
import csv
import locale
import mimetypes
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import List

import pandas as pd
from matplotlib import pyplot as plt
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
    valuation_date: datetime
    balance: float
    num: int

    def __repr__(self):
        return f'Relevé n°{self.num} du {self.valuation_date.strftime("%d %B %Y")};{self.account.type};{self.balance}'


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
    dates = list(set([s.valuation_date for s in statements]))
    dates.sort()
    statements_by_date_pandas = dict()
    for valuation_date in dates:
        solde = sum([s.balance for s in statements for a in accounts if s.account == a and s.valuation_date == valuation_date])
        statement_num: int = list(set([s.num for s in statements if s.valuation_date == valuation_date]))[0]
        date_str = valuation_date.strftime("%d %B %Y")
        print(f'Relevé n°{statement_num} du {date_str:<20s}: {round(solde, 2)}')
        statements_by_date_pandas[valuation_date] = solde

    # Ouvrir le fichier CSV en mode écriture
    with open('statements.csv', mode='w', newline='') as fichier_csv:
        statements_csv = csv.writer(fichier_csv)

        # Écrire les données ligne par ligne
        headers = ["N° de relevé", "Date", "Type de compte", "Solde"]
        statements_csv.writerow(headers)
        for valuation_date in dates:
            statements_by_date: List[Statement] = [s for s in statements if s.valuation_date == valuation_date]
            for s in statements_by_date:
                statements_csv.writerow([s.num, s.valuation_date.date(), s.account.type.name, s.balance])

    # Affichage avec Pandas
    data = {
        'Mois': dates,
        'Solde': [statements_by_date_pandas[d] for d in dates]
    }

    df = pd.DataFrame(data)

    # Affichage sur une période donnée
    # date_debut = '2021-01-02'
    # date_fin = '2023-01-03'
    # donnees_periode = df[(df['Date'] >= date_debut) & (df['Date'] <= date_fin)]

    print(df)

    # Affichage avec matplot lib
    # Mode bâtons (moche)
    # plt.figure(figsize=(8, 4))  # Ajustez la taille du graphique si nécessaire
    # plt.bar(df['Mois'], df['Solde'])
    # plt.xlabel('Mois')
    # plt.ylabel('Solde')
    # plt.title('Solde comptes par mois')
    # plt.show()

    # Mode courbe financière
    plt.figure(figsize=(8, 4))
    plt.plot(df['Mois'], df['Solde'], marker='o', linestyle='-')
    plt.xlabel('Mois')
    plt.ylabel('Solde (en Euros)')
    plt.title('Évolution du solde au fil du temps')
    plt.grid(True)  # Afficher la grille en arrière-plan (facultatif)
    plt.savefig('graphique.png')
    plt.show()