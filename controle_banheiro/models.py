from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Escola(models.Model):
    # Vincula a escola ao professor logado
    professor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="escolas"
    )
    nome = models.CharField(
        max_length=150
    )  # Ex: EE Walkir Vergani, EE Maria da Penha Frugolli
    cidade = models.CharField(max_length=100, default="São Sebastião")

    def __str__(self):
        return self.nome


class Turma(models.Model):
    escola = models.ForeignKey(Escola, on_delete=models.CASCADE, related_name="turmas")
    nome_turma = models.CharField(max_length=50)  # Ex: 2º Ano C, 3º Ano C
    ano_letivo = models.IntegerField(default=2026)

    def __str__(self):
        return f"{self.nome_turma} - {self.escola.nome}"


class Aluno(models.Model):
    SITUACOES = [
        ("Ativo", "Ativo"),
        ("Inativo", "Inativo"),
    ]

    # RELACIONAMENTO NOVO: Vincula o aluno à sua respectiva turma e escola
    turma = models.ForeignKey(
        Turma, on_delete=models.CASCADE, related_name="alunos", null=True, blank=True
    )

    numero_chamada = models.IntegerField()
    nome = models.CharField(max_length=150)
    ra = models.CharField(max_length=20)
    digito_ra = models.CharField(max_length=5)
    situacao = models.CharField(max_length=15, choices=SITUACOES, default="Ativo")

    status = models.CharField(
        max_length=15,
        choices=[("SALA", "Na Sala"), ("FILA", "Na Fila"), ("BANHEIRO", "No Banheiro")],
        default="SALA",
    )

    # Armazena o momento em que o aluno entrou na fila (Garante a ordem FIFO)
    data_entrada_fila = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero_chamada} - {self.nome} ({self.turma.nome_turma if self.turma else 'Sem Turma'})"


class RegistroBanheiro(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="registros")
    data = models.DateField(default=timezone.now)
    hora_saida = models.DateTimeField(auto_now_add=True)
    hora_retorno = models.DateTimeField(null=True, blank=True)
    duracao_minutos = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "registro_banheiro"
        ordering = ["-hora_saida"]

    def save(self, *args, **kwargs):
        # Calcula automaticamente a duração em minutos quando o aluno retorna
        if self.hora_retorno and self.hora_saida:
            diff = self.hora_retorno - self.hora_saida
            self.duracao_minutos = int(diff.total_seconds() / 60)
        super().save(*args, **kwargs)
