# controle_banheiro/admin.py
from django.contrib import admin
from .models import Aluno, RegistroBanheiro, Escola, Turma


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = ("nome", "professor")
    search_fields = ("nome",)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome_turma", "escola")
    list_filter = ("escola",)
    search_fields = ("nome_turma",)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_chamada",
        "nome",
        "turma",
        "get_escola",  # Coluna protegida contra NoneType
        "ra",
        "situacao",
        "status",
    )
    # Mudamos o filtro para 'turma__escola__nome' para evitar falhas de navegação
    list_filter = ("turma__escola__nome", "turma", "status", "situacao")
    search_fields = ("nome", "ra")
    ordering = ("numero_chamada",)

    # Proteção aplicada aqui: valida se turma e escola existem antes de puxar o nome
    @admin.display(ordering="turma__escola__nome", description="Escola")
    def get_escola(self, obj):
        if obj.turma and obj.turma.escola:
            return obj.turma.escola.nome
        return "-"


@admin.register(RegistroBanheiro)
class RegistroBanheiroAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "get_turma",
        "data",
        "hora_saida",
        "hora_retorno",
        "duracao_minutos",
    )
    list_filter = ("data", "aluno__turma")
    date_hierarchy = "data"
    search_fields = ("aluno__nome", "aluno__ra")

    # Proteção aplicada também nos registros de banheiros
    @admin.display(ordering="aluno__turma__nome_turma", description="Turma")
    def get_turma(self, obj):
        if obj.aluno and obj.aluno.turma:
            return obj.aluno.turma.nome_turma
        return "-"
