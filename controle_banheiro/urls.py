from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("sair/<int:aluno_id>/", views.pedir_para_sair, name="pedir_para_sair"),
    path("retornar/<int:aluno_id>/", views.registrar_retorno, name="registrar_retorno"),
    # Novas rotas de relatório
    path("exportar/excel/", views.exportar_excel, name="exportar_excel"),
    path("relatorio/", views.relatorio_analitico_view, name="relatorio_analitico"),
    path("importar-csv/", views.importar_alunos_csv_view, name="importar_csv"),
]
