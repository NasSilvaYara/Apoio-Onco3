"""Cria instituições e conteúdos FICTÍCIOS para testar a busca e o painel.

Uso:  python manage.py popular_exemplo
Os CNPJs e e-mails abaixo são inventados (CNPJ com dígito verificador válido, mas de teste).
As contas de exemplo ficam SEM senha utilizável; para entrar com uma delas use o admin do Django
(ou `python manage.py changepassword <email>`).
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from ongs.models import ConteudoInformativo, Instituicao, TipoApoio
from ongs.validators import gerar_cnpj

EXEMPLOS = [
    dict(base='112223330001', nome='Instituto Mama (exemplo)', tipo='instituto', cidade='Guarulhos', estado='SP',
         bairro='Centro', cep='07010-000', logradouro='Rua das Flores', numero='100', status='ativa',
         descricao='Acolhimento, doação de perucas e apoio social a mulheres em tratamento.',
         horario='Seg a sex, 8h às 17h', telefone='(11) 4000-0001', email='contato@institutomama.example',
         servicos=['Banco de perucas', 'Assistência social']),
    dict(base='223334440001', nome='Casa Lenço Rosa (exemplo)', tipo='casa_apoio', cidade='São Paulo', estado='SP',
         bairro='Vila Mariana', cep='04101-000', logradouro='Av. Exemplo', numero='250', status='ativa',
         descricao='Banco de lenços e acessórios, oficinas de autoestima.',
         horario='Ter a sáb, 9h às 16h', whatsapp='(11) 99999-0002', email='ola@lencorosa.example',
         servicos=['Banco de lenços', 'Apoio psicológico']),
    dict(base='334445550001', nome='Hospital Esperança (exemplo)', tipo='hospital', cidade='Campinas', estado='SP',
         bairro='Cambuí', cep='13025-000', logradouro='Rua da Saúde', numero='45', status='pendente',
         descricao='Serviço de psico-oncologia e grupo de apoio.',
         horario='Seg a sex, 7h às 19h', telefone='(19) 3000-0003', email='psico@hospitalesperanca.example',
         servicos=['Apoio psicológico']),
]


class Command(BaseCommand):
    help = 'Cria dados fictícios de exemplo (instituições e conteúdos).'

    def handle(self, *args, **opts):
        User = get_user_model()
        criadas = 0
        for ex in EXEMPLOS:
            cnpj = gerar_cnpj(ex['base'])
            if Instituicao.objects.filter(cnpj=cnpj).exists():
                continue
            user = User(username=ex['email'], email=ex['email'])
            user.set_unusable_password()
            user.save()
            inst = Instituicao.objects.create(
                usuario=user, cnpj=cnpj, nome=ex['nome'], tipo=ex['tipo'], descricao=ex['descricao'],
                horario_atendimento=ex['horario'], cep=ex['cep'], logradouro=ex['logradouro'],
                numero=ex['numero'], bairro=ex['bairro'], cidade=ex['cidade'], estado=ex['estado'],
                telefone=ex.get('telefone', ''), whatsapp=ex.get('whatsapp', ''),
                email_contato=ex['email'], status=ex['status'],
            )
            inst.servicos.set(TipoApoio.objects.filter(nome__in=ex['servicos']))
            criadas += 1

        ConteudoInformativo.objects.get_or_create(
            titulo='Entenda o câncer (exemplo)',
            defaults=dict(categoria='entenda_cancer', publicado=True,
                          resumo='Informações para conhecer a doença, o tratamento e suas fases.',
                          corpo='Texto de exemplo. Substitua por conteúdo revisado por profissionais de saúde.'),
        )
        self.stdout.write(self.style.SUCCESS(f'{criadas} instituição(ões) de exemplo criada(s).'))
