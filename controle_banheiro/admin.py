from django.contrib import admin
from .models import Aluno, RegistroBanheiro


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("numero_chamada", "nome", "ra", "situacao", "status")
    list_filter = ("status", "situacao")
    search_fields = ("nome", "ra")
    ordering = ("numero_chamada",)


@admin.register(RegistroBanheiro)
class RegistroBanheiroAdmin(admin.ModelAdmin):
    list_display = ("aluno", "data", "hora_saida", "hora_retorno", "duracao_minutos")
    list_filter = ("data",)
    date_hierarchy = "data"
