import csv
import json
import openpyxl
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from django.db import models
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDay
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Aluno, RegistroBanheiro, Turma, Escola


@login_required
def importar_alunos_csv_view(request):
    # Se o método for GET, apenas renderiza a tela com as turmas existentes
    if request.method == "GET":
        return render(request, "controle_banheiro/importar_csv.html")

    # Se for POST, processa o arquivo enviado
    if request.method == "POST":
        nome_escola = request.POST.get("nome_escola", "").strip()
        nome_turma = request.POST.get("nome_turma", "").strip()
        arquivo_csv = request.FILES.get("arquivo_csv")

        # Validações básicas
        if not nome_escola or not nome_turma or not arquivo_csv:
            messages.error(
                request,
                "Por favor, preencha todos os campos e selecione um arquivo CSV.",
            )
            return redirect("importar_csv")

        # 1. Garante que a Escola existe vinculada ao Professor logado
        escola, _ = Escola.objects.get_or_create(
            nome=nome_escola,
            defaults={"professor": request.user},  # Vincula o professor autenticado
        )

        # 2. Garante que a Turma existe dentro dessa escola
        turma, _ = Turma.objects.get_or_create(
            escola=escola,
            nome_turma=nome_turma,
            defaults={"ano_letivo": timezone.now().year},
        )

        try:
            # Lendo o arquivo CSV vindo do upload da SED
            data = arquivo_csv.read().decode("utf-8-sig").splitlines()
            leitor = csv.DictReader(data, delimiter=",")

            alunos_cadastrados = 0
            alunos_atualizados = 0

            for linha in leitor:
                # Trata chaves caso haja espaços invisíveis no cabeçalho do arquivo
                numero_str = linha.get("Nº de chamada", "").strip()
                nome = linha.get("Nome do Aluno", "").strip()
                ra = linha.get("RA", "").strip()
                digito = linha.get("Dig. RA", "").strip()
                situacao = linha.get("Situação do Aluno", "Ativo").strip()

                if not ra:
                    continue  # Pula linhas vazias ou corrompidas do CSV

                numero = int(numero_str) if numero_str.isdigit() else 0

                # update_or_create evita duplicar alunos se o RA já existir na mesma turma
                aluno, criado = Aluno.objects.update_or_create(
                    ra=ra,
                    turma=turma,
                    defaults={
                        "numero_chamada": numero,
                        "nome": nome,
                        "digito_ra": digito,
                        "situacao": situacao,
                        "status": "SALA",  # Todos começam na sala
                    },
                )

                if criado:
                    alunos_cadastrados += 1
                else:
                    alunos_atualizados += 1

            messages.success(
                request,
                f"Sucesso! {alunos_cadastrados} novos alunos cadastrados e {alunos_atualizados} atualizados na turma {nome_turma} da {nome_escola}.",
            )

        except Exception as e:
            messages.error(request, f"Erro ao processar o arquivo CSV: {str(e)}")

        return redirect("importar_csv")


@login_required
def dashboard_view(request):
    # Captura a turma selecionada no filtro
    turma_id = request.GET.get("turma_id", "")

    # Base de alunos ativos do professor logado
    alunos_base = Aluno.objects.filter(
        situacao="Ativo", turma__escola__professor=request.user
    )

    # Se uma turma específica for selecionada, filtra por ela
    if turma_id:
        alunos_em_sala = alunos_base.filter(status="SALA", turma_id=turma_id).order_by(
            "numero_chamada"
        )
        fila_espera = Aluno.objects.filter(
            status="FILA", turma_id=turma_id, turma__escola__professor=request.user
        ).order_by("data_entrada_fila")
        aluno_no_banheiro = Aluno.objects.filter(
            status="BANHEIRO", turma_id=turma_id, turma__escola__professor=request.user
        ).first()
    else:
        # Se não houver filtro, mostra de todas as turmas do professor
        alunos_em_sala = alunos_base.filter(status="SALA").order_by(
            "turma__nome_turma", "numero_chamada"
        )
        fila_espera = Aluno.objects.filter(
            status="FILA", turma__escola__professor=request.user
        ).order_by("data_entrada_fila")
        aluno_no_banheiro = Aluno.objects.filter(
            status="BANHEIRO", turma__escola__professor=request.user
        ).first()

    registro_atual = None
    if aluno_no_banheiro:
        registro_atual = RegistroBanheiro.objects.filter(
            aluno=aluno_no_banheiro, hora_retorno__isnull=True
        ).first()

    context = {
        "alunos_em_sala": alunos_em_sala,
        "fila_espera": fila_espera,
        "aluno_no_banheiro": aluno_no_banheiro,
        "registro_atual": registro_atual,
        "turmas": Turma.objects.filter(escola__professor=request.user).order_by(
            "escola__nome", "nome_turma"
        ),
        "turma_selecionada": turma_id,
    }
    return render(request, "controle_banheiro/dashboard.html", context)


@login_required
def pedir_para_sair(request, aluno_id):
    # Garante que o aluno pertence à escola sob gerência deste professor
    aluno = get_object_or_404(Aluno, id=aluno_id, turma__escola__professor=request.user)

    # Verifica se já tem alguém no banheiro da mesma escola
    banheiro_ocupado = Aluno.objects.filter(
        status="BANHEIRO", turma__escola=aluno.turma.escola
    ).exists()

    if not banheiro_ocupado:
        aluno.status = "BANHEIRO"
        aluno.save()
        RegistroBanheiro.objects.create(aluno=aluno)
    else:
        aluno.status = "FILA"
        aluno.data_entrada_fila = timezone.now()
        aluno.save()

    return redirect("dashboard")


@login_required
def registrar_retorno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id, turma__escola__professor=request.user)

    # Finaliza o registro do aluno atual
    registro = RegistroBanheiro.objects.filter(
        aluno=aluno, hora_retorno__isnull=True
    ).first()
    if registro:
        registro.hora_retorno = timezone.now()
        registro.save()

    aluno.status = "SALA"
    aluno.data_entrada_fila = None
    aluno.save()

    # Regra automática: Próximo da fila (FIFO) restrito à mesma escola
    proximo_aluno = (
        Aluno.objects.filter(status="FILA", turma__escola=aluno.turma.escola)
        .order_by("data_entrada_fila")
        .first()
    )
    if proximo_aluno:
        proximo_aluno.status = "BANHEIRO"
        proximo_aluno.save()
        RegistroBanheiro.objects.create(aluno=proximo_aluno)

    return redirect("dashboard")


@login_required
def exportar_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Histórico de Saídas"

    headers = [
        "Nº Chamada",
        "Nome do Aluno",
        "RA",
        "Data",
        "Hora de Saída",
        "Hora de Retorno",
        "Duração (Min)",
    ]
    ws.append(headers)

    # Filtra histórico apenas dos alunos vinculados a este professor
    registos = RegistroBanheiro.objects.filter(
        hora_retorno__isnull=False, aluno__turma__escola__professor=request.user
    ).order_by("-hora_saida")

    for registo in registos:
        ws.append(
            [
                registo.aluno.numero_chamada,
                registo.aluno.nome,
                f"{registo.aluno.ra}-{registo.aluno.digito_ra}",
                registo.data.strftime("%d/%m/%Y") if registo.data else "",
                registo.hora_saida.strftime("%H:%M:%S") if registo.hora_saida else "",
                (
                    registo.hora_retorno.strftime("%H:%M:%S")
                    if registo.hora_retorno
                    else ""
                ),
                registo.duracao_minutos,
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="relatorio_banheiro.xlsx"'
    wb.save(response)
    return response


@login_required
def relatorio_analitico_view(request):
    busca_aluno = request.GET.get("busca_aluno", "").strip()
    periodo_agrupamento = request.GET.get("periodo", "mes")
    turma_id = request.GET.get("turma_id", "")

    # Base inicial restrita estritamente aos dados do Professor atual
    registros = RegistroBanheiro.objects.filter(
        hora_retorno__isnull=False, aluno__turma__escola__professor=request.user
    )
    alunos = Aluno.objects.filter(
        situacao="Ativo", turma__escola__professor=request.user
    )

    if turma_id:
        registros = registros.filter(aluno__turma_id=turma_id)
        alunos = alunos.filter(turma_id=turma_id)

    if busca_aluno:
        if busca_aluno.isdigit():
            # Corrigido de models.Q para o atalho direto Q importando do módulo principal de db
            registros = registros.filter(
                models.Q(aluno__ra=busca_aluno)
                | models.Q(aluno__numero_chamada=busca_aluno)
            )
            alunos = alunos.filter(
                models.Q(ra=busca_aluno) | models.Q(numero_chamada=busca_aluno)
            )
        else:
            registros = registros.filter(aluno__nome__icontains=busca_aluno)
            alunos = alunos.filter(nome__icontains=busca_aluno)

    # Ranking baseado nos filtros aplicados
    ranking_saidas = (
        alunos.annotate(
            total_saidas=Count("registros"),
            tempo_total=Sum("registros__duracao_minutos"),
        )
        .filter(total_saidas__gt=0)
        .order_by("-total_saidas")
    )

    chart_alunos_labels = [aluno.nome for aluno in ranking_saidas[:10]]
    chart_alunos_valores = [aluno.total_saidas for aluno in ranking_saidas[:10]]

    # Dados temporais dos gráficos
    if periodo_agrupamento == "dia":
        dados_temporais = (
            registros.annotate(periodo=TruncDay("data"))
            .values("periodo")
            .annotate(total=Count("id"))
            .order_by("periodo")
        )
        chart_tempo_labels = [
            item["periodo"].strftime("%d/%m/%Y")
            for item in dados_temporais
            if item["periodo"]
        ]
    else:
        dados_temporais = (
            registros.annotate(periodo=TruncMonth("data"))
            .values("periodo")
            .annotate(total=Count("id"))
            .order_by("periodo")
        )

        if periodo_agrupamento == "bimestre":
            temp_dict = {}
            for item in dados_temporais:
                if item["periodo"]:
                    ano = item["periodo"].year
                    mes = item["periodo"].month
                    bimestre = (mes - 1) // 2 + 1
                    label = f"{bimestre}º Bimestre / {ano}"
                    temp_dict[label] = temp_dict.get(label, 0) + item["total"]
            chart_tempo_labels = list(temp_dict.keys())
            chart_tempo_valores = list(temp_dict.values())
        elif periodo_agrupamento == "semestre":
            temp_dict = {}
            for item in dados_temporais:
                if item["periodo"]:
                    ano = item["periodo"].year
                    mes = item["periodo"].month
                    semestre = 1 if mes <= 6 else 2
                    label = f"{semestre}º Semestre / {ano}"
                    temp_dict[label] = temp_dict.get(label, 0) + item["total"]
            chart_tempo_labels = list(temp_dict.keys())
            chart_tempo_valores = list(temp_dict.values())
        else:
            chart_tempo_labels = [
                item["periodo"].strftime("%m/%Y")
                for item in dados_temporais
                if item["periodo"]
            ]

    if periodo_agrupamento not in ["bimestre", "semestre"]:
        chart_tempo_valores = [
            item["total"] for item in dados_temporais if item["periodo"]
        ]

    context = {
        "ranking_saidas": ranking_saidas,
        "turmas": Turma.objects.filter(escola__professor=request.user),
        "busca_aluno": busca_aluno,
        "periodo_agrupamento": periodo_agrupamento,
        "turma_id": turma_id,
        "chart_alunos_labels": json.dumps(chart_alunos_labels),
        "chart_alunos_valores": json.dumps(chart_alunos_valores),
        "chart_tempo_labels": json.dumps(chart_tempo_labels),
        "chart_tempo_valores": json.dumps(chart_tempo_valores),
    }
    return render(request, "controle_banheiro/relatorio.html", context)
