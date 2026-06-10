from django.db import models
from django.utils import timezone


class Aluno(models.Model):
    SITUACOES = [
        ("Ativo", "Ativo"),
        ("Inativo", "Inativo"),
    ]
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
        return f"{self.numero_chamada} - {self.nome}"


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
