import csv
import os
from django.core.management.base import BaseCommand
from controle_banheiro.models import Aluno


class Command(BaseCommand):
    help = "Importa os alunos a partir do ficheiro filadobanheiro.csv"

    def handle(self, *args, **options):
        # Caminho para o ficheiro na raiz do projeto
        csv_path = os.path.join(os.getcwd(), "filadobanheiro.csv")

        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f"Ficheiro não encontrado em: {csv_path}")
            )
            return

        self.stdout.write(self.style.WARNING("A iniciar a importação dos alunos..."))

        with open(csv_path, mode="r", encoding="utf-8-sig") as file:
            # utf-8-sig remove automaticamente o caractere BOM de arquivos gerados pelo Excel
            reader = csv.DictReader(file)

            contador = 0
            for row in reader:
                # Mapeia as colunas exatas do seu CSV
                Aluno.objects.get_or_create(
                    numero_chamada=int(row["Nº de chamada"]),
                    nome=row["Nome do Aluno"].strip(),
                    ra=row["RA"].strip(),
                    digito_ra=row["Dig. RA"].strip(),
                    situacao=row["Situação do Aluno"].strip(),
                )
                contador += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sucesso! {contador} alunos foram importados para o PostgreSQL."
            )
        )
