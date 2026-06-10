from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)  # <--- Corrigido aqui (404)
from django.utils import timezone
from .models import Aluno, RegistroBanheiro
import openpyxl
from django.http import HttpResponse
from django.db.models import Sum, Count


def dashboard_view(request):
    # Carrega os dados para as 3 colunas do painel
    alunos_em_sala = Aluno.objects.filter(status="SALA", situacao="Ativo").order_by(
        "numero_chamada"
    )
    fila_espera = Aluno.objects.filter(status="FILA").order_by("data_entrada_fila")
    aluno_no_banheiro = Aluno.objects.filter(status="BANHEIRO").first()

    # Pega o registro atual do banheiro para sabermos o horário de saída no frontend
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
    }
    return render(request, "controle_banheiro/dashboard.html", context)


def pedir_para_sair(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)  # <--- Corrigido aqui (404)

    # Verifica se já tem alguém no banheiro
    banheiro_ocupado = Aluno.objects.filter(status="BANHEIRO").exists()

    if not banheiro_ocupado:
        # Banheiro livre: vai direto
        aluno.status = "BANHEIRO"
        aluno.save()
        # Inicia o registro de tempo
        RegistroBanheiro.objects.create(aluno=aluno)
    else:
        # Banheiro ocupado: vai para a fila
        aluno.status = "FILA"
        aluno.data_entrada_fila = timezone.now()
        aluno.save()

    return redirect("dashboard")


def registrar_retorno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)  # <--- Corrigido aqui (404)

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

    # Regra automática: Próximo da fila (FIFO)
    proximo_aluno = (
        Aluno.objects.filter(status="FILA").order_by("data_entrada_fila").first()
    )
    if proximo_aluno:
        proximo_aluno.status = "BANHEIRO"
        proximo_aluno.save()
        # Inicia o registro de tempo para o próximo
        RegistroBanheiro.objects.create(aluno=proximo_aluno)

    return redirect("dashboard")


def exportar_excel(request):
    # Cria um novo livro de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Histórico de Saídas"

    # Define o cabeçalho da tabela
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

    # Procura todos os registos finalizados no Postgres
    registos = RegistroBanheiro.objects.filter(hora_retorno__isnull=False).order_by(
        "-hora_saida"
    )

    for registo in registos:
        ws.append(
            [
                registo.aluno.numero_chamada,
                registo.aluno.nome,
                f"{registo.aluno.ra}-{registo.aluno.digito_ra}",
                registo.data.strftime("%d/%m/%Y"),
                registo.hora_saida.strftime("%H:%M:%S"),
                registo.hora_retorno.strftime("%H:%M:%S"),
                registo.duracao_minutos,
            ]
        )

    # Configura a resposta HTTP para o navegador fazer o download do ficheiro
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="relatorio_banheiro.xlsx"'
    wb.save(response)
    return response


def relatorio_analitico_view(request):
    # Agrupa os alunos que mais vezes saíram e o tempo total acumulado por cada um
    ranking_saidas = (
        Aluno.objects.annotate(
            total_saidas=Count("registros"),
            tempo_total=Sum("registros__duracao_minutos"),
        )
        .filter(total_saidas__gt=0)
        .order_by("-total_saidas")
    )

    context = {"ranking_saidas": ranking_saidas}
    return render(request, "controle_banheiro/relatorio.html", context)
