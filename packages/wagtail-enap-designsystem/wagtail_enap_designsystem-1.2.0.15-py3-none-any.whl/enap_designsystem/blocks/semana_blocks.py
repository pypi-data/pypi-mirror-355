from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
# REMOVIDO: from wagtail.admin.panels import StreamFieldPanel, FieldPanel
from wagtail.blocks import (
    CharBlock, TextBlock, RichTextBlock, URLBlock, 
    StructBlock, ListBlock, BooleanBlock, IntegerBlock, 
    DateBlock, EmailBlock
)


# =============================================================================
# PALETA DE CORES PERSONALIZADA
# =============================================================================

# Cores principais da paleta
BRAND_INOVACAO_CHOICES = [
    ('#173039', 'Verde Musgo Escuro'),
    ('#3A8A9C', 'Azul Petróleo'),
    ('#25552A', 'Verde Floresta Escuro'),
    ('#818C27', 'Verde Oliva'),
    ('#FF7A1B', 'Laranja Vibrante'),
    ('#FFEB31', 'Amarelo Canário'),
    ('#FFF0D9', 'Creme Suave'),
    ('#DB8C3F', 'Dourado Queimado'),
    ('#990005', 'Vermelho Bordô'),
    ('#EA1821', 'Vermelho Cereja'),
]

# Cores para textos (tons mais escuros e legíveis)
BRAND_TEXTS_CHOICES = [
    ('#173039', 'Verde Musgo Escuro'),
    ('#00777D', 'Enap'),
    ('#58606E', 'Enap Cinza'),
    ('#AFF0ED', 'Enap Azul'),
    ('#25552A', 'Verde Floresta Escuro'),
    ('#818C27', 'Verde Oliva'),
    ('#DB8C3F', 'Dourado Queimado'),
    ('#990005', 'Vermelho Bordô'),
    ('#000000', 'Preto'),
    ('#2F2F2F', 'Cinza Escuro'),
    ('#4A4A4A', 'Cinza Médio'),
]

# Cores para backgrounds (incluindo tons claros)
BRAND_BG_CHOICES = [
    ('#173039', 'Verde Musgo Escuro'),
    ('#F5F7FA', 'Azul Enap'),
    ('#FCFCFC', 'Cinza Enap'),
    ('#3A8A9C', 'Azul Petróleo'),
    ('#25552A', 'Verde Floresta Escuro'),
    ('#818C27', 'Verde Oliva'),
    ('#FF7A1B', 'Laranja Vibrante'),
    ('#FFEB31', 'Amarelo Canário'),
    ('#FFF0D9', 'Creme Suave'),
    ('#DB8C3F', 'Dourado Queimado'),
    ('#990005', 'Vermelho Bordô'),
    ('#EA1821', 'Vermelho Cereja'),
    ('#FFFFFF', 'Branco'),
    ('#F8F9FA', 'Cinza Muito Claro'),
]

# Cores para botões e elementos interativos
BRAND_BUTTON_CHOICES = [
    ('#FF7A1B', 'Laranja Vibrante'),
    ('#FFEB31', 'Amarelo Canário'),
    ('#3A8A9C', 'Azul Petróleo'),
    ('#818C27', 'Verde Oliva'),
    ('#DB8C3F', 'Dourado Queimado'),
    ('#EA1821', 'Vermelho Cereja'),
    ('#25552A', 'Verde Floresta Escuro'),
]

# Cores para hover dos botões
BRAND_HOVER_CHOICES = [
    ('#E6690F', 'Laranja Escuro'),
    ('#E6D220', 'Amarelo Escuro'),
    ('#2E7A8A', 'Azul Petróleo Escuro'),
    ('#6F7B22', 'Verde Oliva Escuro'),
    ('#C27B35', 'Dourado Escuro'),
    ('#D1141B', 'Vermelho Cereja Escuro'),
    ('#1E4420', 'Verde Floresta Muito Escuro'),
]


# =============================================================================
# BLOCKS REUTILIZÁVEIS DA SEMANA DE INOVAÇÃO
# =============================================================================

class ImageBlock(StructBlock):
    """Block simples de imagem"""
    imagem = ImageChooserBlock(label="Imagem")
    alt_text = CharBlock(label="Texto Alternativo", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/image_block.html'
        icon = 'image'
        label = 'Imagem'


class ParticipanteBlock(StructBlock):
    """Block de participante individual"""
    nome = CharBlock(label="Nome Completo")
    cargo = CharBlock(label="Cargo/Função", required=False)
    empresa = CharBlock(label="Empresa/Organização", required=False)
    foto = ImageChooserBlock(label="Foto do Participante")
    descricao = RichTextBlock(label="Biografia", required=False)
    
    # Redes sociais
    link_linkedin = URLBlock(label="LinkedIn", required=False)
    link_instagram = URLBlock(label="Instagram", required=False)
    link_twitter = URLBlock(label="Twitter/X", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/participantes.html'
        icon = 'user'
        label = 'Participante'


class StatBlock(StructBlock):
    """Block para estatísticas/números"""
    valor = CharBlock(label="Valor", help_text="Ex: 129, 500+")
    descricao = CharBlock(label="Descrição", help_text="Ex: Atividades, Participantes")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/stat_block.html'
        icon = 'plus'
        label = 'Estatística'


class GaleriaFotoBlock(StructBlock):
    """Block para foto da galeria"""
    imagem = ImageChooserBlock(label="Imagem")
    descricao = CharBlock(label="Descrição", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/galeria_foto_block.html'
        icon = 'image'
        label = 'Foto da Galeria'


class FAQItemBlock(StructBlock):
    """Item individual de FAQ"""
    question = CharBlock(label="Pergunta")
    answer = RichTextBlock(label="Resposta")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/faq_item_block.html'
        icon = 'help'
        label = 'Item FAQ'


class FAQTabBlock(StructBlock):
    """Aba de FAQ com múltiplos itens"""
    tab_name = CharBlock(label="Nome da Aba")
    faq_items = ListBlock(FAQItemBlock(), label="Itens do FAQ")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/faq_tab_block.html'
        icon = 'folder-open-1'
        label = 'Aba FAQ'


class AtividadeBlock(StructBlock):
    """Block para atividade da programação"""
    horario_inicio = CharBlock(label="Horário de Início", help_text="Ex: 09:00")
    horario_fim = CharBlock(label="Horário de Fim", help_text="Ex: 10:00")
    titulo = CharBlock(label="Título da Atividade")
    descricao = TextBlock(label="Descrição", required=False)
    
    # Tipo de atividade
    TIPO_CHOICES = [
        ('online', 'Online'),
        ('presencial', 'Presencial'),
    ]
    tipo = CharBlock(label="Tipo", help_text="Digite: online ou presencial")
    
    # Local (para presencial) ou tag (para online)
    local_tag = CharBlock(label="Local/Tag", help_text="Ex: Sala 106, On-Line")
    
    # Data da atividade
    data = DateBlock(label="Data da Atividade")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/atividade_block.html'
        icon = 'time'
        label = 'Atividade'


class HospitalityCardBlock(StructBlock):
    """Card de hospitalidade/serviços"""
    title = CharBlock(label="Título")
    text = RichTextBlock(label="Texto")
    image = ImageChooserBlock(label="Imagem")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/hospitality_card_block.html'
        icon = 'home'
        label = 'Card de Hospitalidade'


class VideoBlock(StructBlock):
    """Block para vídeo"""
    titulo = CharBlock(label="Título do Vídeo")
    video_url = URLBlock(label="URL do Vídeo")
    descricao = TextBlock(label="Descrição", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/video_block.html'
        icon = 'media'
        label = 'Vídeo'


class CertificadoBlock(StructBlock):
    """Block para seção de certificado"""
    titulo = CharBlock(label="Título")
    texto = RichTextBlock(label="Texto")
    texto_botao = CharBlock(label="Texto do Botão", default="Baixar certificado")
    imagem = ImageChooserBlock(label="Imagem do Certificado")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/certificado_block.html'
        icon = 'doc-full'
        label = 'Certificado'


class NewsletterBlock(StructBlock):
    """Block para newsletter"""
    titulo = CharBlock(label="Título", default="ASSINE NOSSA NEWSLETTER")
    texto = RichTextBlock(label="Texto")
    imagem = ImageChooserBlock(label="Imagem", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/newsletter_block.html'
        icon = 'mail'
        label = 'Newsletter'


class ContatoBlock(StructBlock):
    """Block para seção de contato"""
    titulo = CharBlock(label="Título", default="FALE CONOSCO")
    texto = RichTextBlock(label="Texto")

    class Meta:
        template = 'enap_designsystem/semana_inovacao/contato_block.html'
        icon = 'mail'
        label = 'Contato'


class FooterBlock(StructBlock):
    """Block para footer"""
    logo = ImageChooserBlock(label="Logo")
    texto_evento = RichTextBlock(label="Texto do Evento")
    logo_hero_link = URLBlock(label="Link do Logo", required=False)

    class Meta:
        template = 'enap_designsystem/semana_inovacao/footer_block.html'
        icon = 'list-ul'
        label = 'Footer'


# =============================================================================
# SEMANA DE INOVAÇÃO - BLOCOS CUSTOMIZADOS
# =============================================================================

class BannerConcurso(blocks.StructBlock):
    """
    StructBlock para criar um banner de concurso
    """
    
    titulo = blocks.CharBlock(
        required=True,
        max_length=100,
        help_text="Título principal do banner"
    )
    
    subtitulo = blocks.CharBlock(
        required=False,
        max_length=200,
        help_text="Subtítulo ou descrição do banner"
    )
    
    imagem_fundo = ImageChooserBlock(
        required=True,
        help_text="Imagem de fundo do banner"
    )
    
    imagem_principal = ImageChooserBlock(
        required=True,
        help_text="Imagem principal do banner"
    )
    
    imagem_secundaria = ImageChooserBlock(
        required=True,
        help_text="Segunda imagem do banner"
    )
    
    link = blocks.URLBlock(
        required=False,
        help_text="URL para onde o banner deve direcionar (opcional)"
    )
    
    texto_link = blocks.CharBlock(
        required=False,
        max_length=50,
        help_text="Texto do botão/link (ex: 'Saiba mais')"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFF0D9',
        help_text="Cor de fundo do conteúdo do banner"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    cor_subtitulo = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do subtítulo"
    )
    
    cor_botao = blocks.ChoiceBlock(
        choices=BRAND_BUTTON_CHOICES,
        default='#FF7A1B',
        help_text="Cor do botão"
    )
    
    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_banner.html'
        icon = 'image'
        label = 'Banner de Concurso'
        help_text = 'Banner personalizado para concursos'


class MaterialApioBlock(blocks.StructBlock):
    """Bloco para Material de Apoio com layout personalizado"""
    
    # Configurações gerais
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#173039',
        help_text="Cor de fundo da seção"
    )

    cor_texto_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do título"
    )
    
    # Conteúdo principal (lado esquerdo)
    titulo = blocks.CharBlock(
        max_length=100,
        help_text="Título principal da seção"
    )
    texto = blocks.TextBlock(
        help_text="Texto descritivo da seção"
    )
    email_contato = blocks.EmailBlock(
        required=False,
        help_text="Email de contato (opcional)"
    )
    
    cor_texto = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do texto"
    )
    
    # Card com imagem (lado direito)
    imagem_card = ImageChooserBlock(
        help_text="Imagem do card lateral"
    )
    link_card = blocks.URLBlock(
        help_text="Link para onde a imagem deve direcionar"
    )
    alt_imagem = blocks.CharBlock(
        max_length=100,
        default="Imagem do material de apoio",
        help_text="Texto alternativo da imagem"
    )
    
    # StreamField de Botões
    botoes = blocks.StreamBlock([
        ('botao', blocks.StructBlock([
            ('texto', blocks.CharBlock(
                max_length=100,
                help_text="Texto do botão"
            )),
            ('link', blocks.URLBlock(
                help_text="URL para onde o botão deve direcionar"
            )),
            ('cor_fundo', blocks.ChoiceBlock(
                choices=BRAND_BUTTON_CHOICES,
                default='#FFEB31',
                help_text="Cor de fundo do botão"
            )),
            ('cor_hover', blocks.ChoiceBlock(
                choices=BRAND_HOVER_CHOICES,
                default='#E6D220',
                help_text="Cor do botão ao passar o mouse"
            )),
            ('cor_texto', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#173039',
                help_text="Cor do texto do botão"
            )),
        ], icon='link', label='Botão')),
    ], 
    min_num=1,
    help_text="Adicione quantos botões quiser"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_material_apoio.html'
        icon = 'doc-full'
        label = 'Material de Apoio'


class SecaoPatrocinadoresBlock(blocks.StructBlock):
    
    # Imagem de background
    imagem_background = ImageChooserBlock(
        help_text="Imagem de fundo da seção"
    )
    
    # Título e cor
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título principal da seção"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do título"
    )
    
    # Imagem em destaque
    imagem_destaque = ImageChooserBlock(
        help_text="Imagem principal em destaque"
    )
    
    # StreamField de fotos
    galeria_fotos = blocks.StreamBlock([
        ('foto', blocks.StructBlock([
            ('imagem', ImageChooserBlock(
                help_text="Imagem da galeria"
            )),
        ], icon='image', label='Foto')),
    ], 
    min_num=0,
    help_text="Adicione quantas fotos quiser na galeria"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_patrocinadores.html'
        icon = 'image'
        label = 'Seção com Destaque'


class SecaoApresentacaoBlock(blocks.StructBlock):
    """Bloco para seção de apresentação com título, subtítulo, foto e rich text"""
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFF0D9',
        help_text="Cor de fundo da seção"
    )
    
    posicao_imagem = blocks.ChoiceBlock(
        choices=[
            ('direita', 'Imagem à Direita'),
            ('esquerda', 'Imagem à Esquerda'),
        ],
        default='direita',
        help_text="Posição da imagem em relação ao texto"
    )
    
    # Título principal
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título principal da seção"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#818C27',
        help_text="Cor do título principal"
    )
    
    # Subtítulo (opcional)
    subtitulo = blocks.CharBlock(
        max_length=300,
        required=False,
        help_text="Subtítulo da seção (opcional)"
    )
    
    cor_subtitulo = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#173039',
        help_text="Cor do subtítulo"
    )
    
    # Foto circular
    imagem_circular = ImageChooserBlock(
        help_text="Imagem que aparecerá em formato circular"
    )
    
    alt_imagem = blocks.CharBlock(
        max_length=100,
        default="Imagem ilustrativa",
        help_text="Texto alternativo da imagem"
    )
    
    # Rich Text para conteúdo
    conteudo = blocks.RichTextBlock(
        features=['bold', 'italic', 'link', 'ol', 'ul', 'hr', 'document-link'],
        help_text="Conteúdo principal em rich text",
        required=False
    )
    
    cor_texto = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do texto do conteúdo"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_secao_apresentacao.html'
        icon = 'doc-full'
        label = 'Seção Apresentação'


class SecaoCategoriasBlock(blocks.StructBlock):
    """Bloco para seção com imagem no topo e duas colunas de categorias"""
    
    # Configurações de fundo
    imagem_fundo = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo da seção (opcional)"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFFFFF',
        help_text="Cor de fundo da seção"
    )
    
    # Imagem no topo
    imagem_topo = ImageChooserBlock(
        help_text="Imagem que ocupará toda a largura no topo"
    )
    
    alt_imagem = blocks.CharBlock(
        max_length=100,
        default="Imagem ilustrativa",
        help_text="Texto alternativo da imagem"
    )
    
    # Primeira coluna
    titulo_coluna_1 = blocks.CharBlock(
        max_length=200,
        help_text="Título da primeira coluna"
    )
    
    cor_titulo_1 = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título da primeira coluna"
    )
    
    conteudo_coluna_1 = blocks.RichTextBlock(
        features=['bold', 'italic', 'link', 'ol', 'ul', 'hr'],
        help_text="Conteúdo da primeira coluna"
    )
    
    cor_texto_1 = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do texto da primeira coluna"
    )
    
    # Segunda coluna
    titulo_coluna_2 = blocks.CharBlock(
        max_length=200,
        help_text="Título da segunda coluna"
    )
    
    cor_titulo_2 = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título da segunda coluna"
    )
    
    conteudo_coluna_2 = blocks.RichTextBlock(
        features=['bold', 'italic', 'link', 'ol', 'ul', 'hr'],
        help_text="Conteúdo da segunda coluna"
    )
    
    cor_texto_2 = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do texto da segunda coluna"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_secao_categorias.html'
        icon = 'doc-full-inverse'
        label = 'Seção Categorias'


class CronogramaBlock(blocks.StructBlock):
    """Bloco para cronograma com steps flexíveis"""
    
    # Configurações de fundo
    imagem_fundo = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo da seção (opcional)"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFF0D9',
        help_text="Cor de fundo da seção"
    )
    
    # Título da seção
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título do cronograma (ex: De olho no cronograma)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    # StreamField para os steps
    steps = blocks.StreamBlock([
        ('step', blocks.StructBlock([
            ('data', blocks.CharBlock(
                max_length=50,
                help_text="Data do step (ex: 05 MAI)"
            )),
            ('cor_data', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#173039',
                help_text="Cor do texto da data"
            )),
            ('cor_circulo', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#818C27',
                help_text="Cor do círculo"
            )),
            ('descricao', blocks.TextBlock(
                max_length=300,
                help_text="Descrição do step"
            )),
            ('cor_descricao', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#25552A',
                help_text="Cor do texto da descrição"
            )),
        ], icon='date', label='Step do Cronograma')),
    ], 
    min_num=2,
    max_num=10,
    help_text="Adicione entre 2 e 10 steps no cronograma"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_cronograma.html'
        icon = 'time'
        label = 'Cronograma'


class SecaoPremiosBlock(blocks.StructBlock):
    """Bloco para seção de prêmios com imagem de fundo e lista de tópicos"""
    
    # Configurações de fundo
    imagem_fundo = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo da seção (opcional)"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFFFFF',
        help_text="Cor de fundo da seção"
    )
    
    # Título da seção
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título da seção (ex: Quais são os prêmios?)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    cor_topicos = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do texto dos tópicos"
    )
    
    topicos = blocks.StreamBlock([
        ('topico', blocks.TextBlock(
            max_length=500,
            help_text="Texto do tópico/prêmio"
        )),
    ], 
    min_num=1,
    max_num=15,
    help_text="Adicione os tópicos/prêmios (até 15 itens)"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_secao_premios.html'
        icon = 'trophy'
        label = 'Seção Prêmios'


class SecaoFAQBlock(blocks.StructBlock):
    """Bloco para seção de FAQ com accordion"""
    
    # Configurações de fundo
    imagem_fundo = ImageChooserBlock(
        required=False,
        help_text="Imagem de fundo da seção (opcional)"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFF0D9',
        help_text="Cor de fundo da seção"
    )
    
    # Título da seção
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título da seção (ex: Perguntas Frequentes)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    # Cor das perguntas
    cor_perguntas = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#173039',
        help_text="Cor do texto das perguntas"
    )
    
    # Cor das respostas
    cor_respostas = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#25552A',
        help_text="Cor do texto das respostas"
    )
    
    # Cor do accordion
    cor_accordion = blocks.ChoiceBlock(
        choices=BRAND_BUTTON_CHOICES,
        default='#FF7A1B',
        help_text="Cor de destaque do accordion"
    )
    
    # StreamField para as FAQs
    faqs = blocks.StreamBlock([
        ('faq', blocks.StructBlock([
            ('pergunta', blocks.CharBlock(
                max_length=300,
                help_text="Pergunta do FAQ"
            )),
            ('resposta', blocks.RichTextBlock(
                features=['bold', 'italic', 'link', 'ol', 'ul'],
                help_text="Resposta da pergunta"
            )),
        ], icon='help', label='FAQ')),
    ], 
    min_num=1,
    max_num=20,
    help_text="Adicione as perguntas e respostas (até 20 itens)"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_secao_faq.html'
        icon = 'help'
        label = 'Seção FAQ'


class SecaoContatoBlock(blocks.StructBlock):
    """Bloco para seção de contato com imagem e formulário"""
    
    # Configurações de fundo
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#173039',
        help_text="Cor de fundo da seção"
    )
    
    # Imagem lateral
    imagem = ImageChooserBlock(
        help_text="Imagem que ficará na lateral esquerda"
    )
    
    alt_imagem = blocks.CharBlock(
        max_length=100,
        default="Imagem ilustrativa",
        help_text="Texto alternativo da imagem"
    )
    
    # Títulos do formulário
    titulo_principal = blocks.CharBlock(
        max_length=100,
        help_text="Título principal (ex: Fale Conosco)"
    )
    
    cor_titulo_principal = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do título principal"
    )
    
    subtitulo = blocks.CharBlock(
        max_length=200,
        help_text="Subtítulo do formulário (ex: Envie sua mensagem)"
    )
    
    cor_subtitulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#818C27',
        help_text="Cor do subtítulo"
    )
    
    # Configurações do formulário
    cor_botao = blocks.ChoiceBlock(
        choices=BRAND_BUTTON_CHOICES,
        default='#FFEB31',
        help_text="Cor do botão de enviar"
    )
    
    cor_hover_botao = blocks.ChoiceBlock(
        choices=BRAND_HOVER_CHOICES,
        default='#E6D220',
        help_text="Cor do botão ao passar o mouse"
    )
    
    cor_texto_botao = blocks.ChoiceBlock(
        choices=BRAND_TEXTS_CHOICES,
        default='#173039',
        help_text="Cor do texto do botão"
    )
    
    texto_botao = blocks.CharBlock(
        max_length=50,
        default="Enviar",
        help_text="Texto do botão"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_secao_contato.html'
        icon = 'mail'
        label = 'Seção Contato'


class MenuNavigationBlock(blocks.StructBlock):
    """Bloco para menu de navegação customizado"""
    
    items_menu = blocks.ListBlock(
        blocks.StructBlock([
            ('texto', blocks.CharBlock(max_length=50, help_text="Texto do menu")),
            ('url', blocks.URLBlock(required=False, help_text="URL externa")),
            ('pagina_interna', blocks.PageChooserBlock(required=False, help_text="Ou escolha uma página interna")),
            ('ativo', blocks.BooleanBlock(required=False, default=False, help_text="Marcar como item ativo")),
        ]),
        min_num=1,
        max_num=10,
        help_text="Itens do menu de navegação"
    )
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#173039',
        help_text="Cor de fundo do menu"
    )
    
    cor_texto = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do texto do menu"
    )
    
    cor_ativo = blocks.ChoiceBlock(
        choices=BRAND_BUTTON_CHOICES,
        default='#FF7A1B',
        help_text="Cor do item ativo"
    )
    
    cor_hover = blocks.ChoiceBlock(
        choices=BRAND_BUTTON_CHOICES,
        default='#FFEB31',
        help_text="Cor do hover nos itens"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/blocks_menu_navigation.html'
        icon = 'list-ul'
        label = 'Menu de Navegação'


class SecaoTestemunhosBlock(blocks.StructBlock):
    """Bloco para seção de testemunhos/depoimentos"""
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFF0D9',
        help_text="Cor de fundo da seção"
    )
    
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título da seção (ex: O que dizem sobre nós)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    testemunhos = blocks.StreamBlock([
        ('testemunho', blocks.StructBlock([
            ('nome', blocks.CharBlock(
                max_length=100,
                help_text="Nome da pessoa"
            )),
            ('cargo', blocks.CharBlock(
                max_length=150,
                help_text="Cargo/posição da pessoa"
            )),
            ('foto', ImageChooserBlock(
                help_text="Foto da pessoa"
            )),
            ('depoimento', blocks.TextBlock(
                help_text="Texto do depoimento"
            )),
            ('cor_nome', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#173039',
                help_text="Cor do nome"
            )),
            ('cor_cargo', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#25552A',
                help_text="Cor do cargo"
            )),
            ('cor_depoimento', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#25552A',
                help_text="Cor do texto do depoimento"
            )),
        ], icon='user', label='Testemunho')),
    ], 
    min_num=1,
    max_num=6,
    help_text="Adicione até 6 testemunhos"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_testemunhos.html'
        icon = 'openquote'
        label = 'Seção Testemunhos'


class SecaoEstatisticasBlock(blocks.StructBlock):
    """Bloco para seção de estatísticas/números importantes"""
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#173039',
        help_text="Cor de fundo da seção"
    )
    
    titulo = blocks.CharBlock(
        max_length=200,
        required=False,
        help_text="Título da seção (opcional)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do título"
    )
    
    estatisticas = blocks.StreamBlock([
        ('estatistica', blocks.StructBlock([
            ('numero', blocks.CharBlock(
                max_length=20,
                help_text="Número/valor (ex: 500+, 95%)"
            )),
            ('descricao', blocks.CharBlock(
                max_length=100,
                help_text="Descrição do número"
            )),
            ('cor_numero', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#FFEB31',
                help_text="Cor do número"
            )),
            ('cor_descricao', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#FFF0D9',
                help_text="Cor da descrição"
            )),
        ], icon='plus', label='Estatística')),
    ], 
    min_num=2,
    max_num=8,
    help_text="Adicione entre 2 e 8 estatísticas"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_estatisticas.html'
        icon = 'snippet'
        label = 'Seção Estatísticas'


class SecaoCardsBlock(blocks.StructBlock):
    """Bloco para seção com cards flexíveis"""
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFFFFF',
        help_text="Cor de fundo da seção"
    )
    
    titulo = blocks.CharBlock(
        max_length=200,
        required=False,
        help_text="Título da seção (opcional)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    cards = blocks.StreamBlock([
        ('card', blocks.StructBlock([
            ('imagem', ImageChooserBlock(
                help_text="Imagem do card"
            )),
            ('titulo_card', blocks.CharBlock(
                max_length=100,
                help_text="Título do card"
            )),
            ('texto', blocks.TextBlock(
                help_text="Texto descritivo do card"
            )),
            ('link', blocks.URLBlock(
                required=False,
                help_text="Link do card (opcional)"
            )),
            ('texto_link', blocks.CharBlock(
                max_length=50,
                required=False,
                default="Saiba mais",
                help_text="Texto do link"
            )),
            ('cor_titulo_card', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#173039',
                help_text="Cor do título do card"
            )),
            ('cor_texto', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#25552A',
                help_text="Cor do texto"
            )),
            ('cor_link', blocks.ChoiceBlock(
                choices=BRAND_BUTTON_CHOICES,
                default='#FF7A1B',
                help_text="Cor do link"
            )),
            ('cor_fundo_card', blocks.ChoiceBlock(
                choices=BRAND_BG_CHOICES,
                default='#FFF0D9',
                help_text="Cor de fundo do card"
            )),
        ], icon='doc-full', label='Card')),
    ], 
    min_num=1,
    max_num=12,
    help_text="Adicione até 12 cards"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_cards.html'
        icon = 'grip'
        label = 'Seção Cards'


class SecaoTimelineBlock(blocks.StructBlock):
    """Bloco para seção de timeline/linha do tempo"""
    
    cor_fundo = blocks.ChoiceBlock(
        choices=BRAND_BG_CHOICES,
        default='#FFFFFF',
        help_text="Cor de fundo da seção"
    )
    
    titulo = blocks.CharBlock(
        max_length=200,
        help_text="Título da seção"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#173039',
        help_text="Cor do título"
    )
    
    cor_linha = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#3A8A9C',
        help_text="Cor da linha do tempo"
    )
    
    eventos = blocks.StreamBlock([
        ('evento', blocks.StructBlock([
            ('data', blocks.CharBlock(
                max_length=50,
                help_text="Data do evento (ex: Jan 2024)"
            )),
            ('titulo_evento', blocks.CharBlock(
                max_length=150,
                help_text="Título do evento"
            )),
            ('descricao', blocks.TextBlock(
                help_text="Descrição do evento"
            )),
            ('cor_data', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#FF7A1B',
                help_text="Cor da data"
            )),
            ('cor_titulo_evento', blocks.ChoiceBlock(
                choices=BRAND_INOVACAO_CHOICES,
                default='#173039',
                help_text="Cor do título do evento"
            )),
            ('cor_descricao', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#25552A',
                help_text="Cor da descrição"
            )),
            ('cor_circulo', blocks.ChoiceBlock(
                choices=BRAND_BUTTON_CHOICES,
                default='#FFEB31',
                help_text="Cor do círculo na linha"
            )),
        ], icon='date', label='Evento')),
    ], 
    min_num=2,
    max_num=15,
    help_text="Adicione entre 2 e 15 eventos na timeline"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_timeline.html'
        icon = 'time'
        label = 'Seção Timeline'


class SecaoHeroBannerBlock(blocks.StructBlock):
    """Bloco para hero banner principal"""
    
    imagem_fundo = ImageChooserBlock(
        help_text="Imagem de fundo do hero banner"
    )
    
    titulo_principal = blocks.CharBlock(
        max_length=150,
        help_text="Título principal do banner"
    )
    
    subtitulo = blocks.CharBlock(
        max_length=300,
        required=False,
        help_text="Subtítulo (opcional)"
    )
    
    texto_descricao = blocks.TextBlock(
        required=False,
        help_text="Texto descritivo (opcional)"
    )
    
    cor_titulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do título principal"
    )
    
    cor_subtitulo = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFEB31',
        help_text="Cor do subtítulo"
    )
    
    cor_texto = blocks.ChoiceBlock(
        choices=BRAND_INOVACAO_CHOICES,
        default='#FFF0D9',
        help_text="Cor do texto descritivo"
    )
    
    # Botões do hero
    botoes_hero = blocks.StreamBlock([
        ('botao_hero', blocks.StructBlock([
            ('texto_botao', blocks.CharBlock(
                max_length=50,
                help_text="Texto do botão"
            )),
            ('link_botao', blocks.URLBlock(
                help_text="Link do botão"
            )),
            ('tipo_botao', blocks.ChoiceBlock(
                choices=[
                    ('primario', 'Primário'),
                    ('secundario', 'Secundário'),
                    ('outline', 'Outline'),
                ],
                default='primario',
                help_text="Tipo/estilo do botão"
            )),
            ('cor_fundo_botao', blocks.ChoiceBlock(
                choices=BRAND_BUTTON_CHOICES,
                default='#FF7A1B',
                help_text="Cor de fundo do botão"
            )),
            ('cor_texto_botao', blocks.ChoiceBlock(
                choices=BRAND_TEXTS_CHOICES,
                default='#173039',
                help_text="Cor do texto do botão"
            )),
            ('cor_hover_botao', blocks.ChoiceBlock(
                choices=BRAND_HOVER_CHOICES,
                default='#E6690F',
                help_text="Cor do hover do botão"
            )),
        ], icon='link', label='Botão Hero')),
    ], 
    min_num=0,
    max_num=3,
    help_text="Adicione até 3 botões no hero banner"
    )
    
    # Overlay/sobreposição
    overlay_opacity = blocks.ChoiceBlock(
        choices=[
            ('0', 'Sem overlay'),
            ('0.3', 'Overlay leve'),
            ('0.5', 'Overlay médio'),
            ('0.7', 'Overlay forte'),
        ],
        default='0.5',
        help_text="Opacidade do overlay escuro sobre a imagem"
    )

    class Meta:
        template = 'enap_designsystem/semana_inovacao/block_hero_banner.html'
        icon = 'image'
        label = 'Hero Banner'


# =============================================================================
# STREAMFIELD CHOICES PARA USO EM PÁGINAS
# =============================================================================

SEMANA_INOVACAO_STREAMFIELD_CHOICES = [
    # Blocos principais
    ('hero_banner', SecaoHeroBannerBlock()),
    ('banner_concurso', BannerConcurso()),
    
    # Blocos de conteúdo
    ('secao_apresentacao', SecaoApresentacaoBlock()),
    ('secao_categorias', SecaoCategoriasBlock()),
    ('secao_cards', SecaoCardsBlock()),
    ('material_apoio', MaterialApioBlock()),
    
    # Blocos informativos
    ('cronograma', CronogramaBlock()),
    ('secao_premios', SecaoPremiosBlock()),
    ('secao_faq', SecaoFAQBlock()),
    ('timeline', SecaoTimelineBlock()),
    
    # Blocos de engajamento
    ('secao_testemunhos', SecaoTestemunhosBlock()),
    ('secao_estatisticas', SecaoEstatisticasBlock()),
    ('secao_contato', SecaoContatoBlock()),
    
    # Blocos utilitários
    ('secao_patrocinadores', SecaoPatrocinadoresBlock()),
    ('menu_navigation', MenuNavigationBlock()),
    
    # Blocos básicos reutilizáveis
    ('imagem', ImageBlock()),
    ('participante', ParticipanteBlock()),
    ('galeria_foto', GaleriaFotoBlock()),
    ('video', VideoBlock()),
    ('certificado', CertificadoBlock()),
    ('newsletter', NewsletterBlock()),
    ('contato', ContatoBlock()),
    ('footer', FooterBlock()),
]