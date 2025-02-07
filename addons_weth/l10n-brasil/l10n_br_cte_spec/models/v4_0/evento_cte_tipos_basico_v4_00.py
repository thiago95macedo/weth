# Copyright 2023 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated by https://github.com/akretion/xsdata-odoo
#
import textwrap
from odoo import fields, models
from .tipos_geral_cte_v4_00 import (
    TAMB,
    TCORGAOIBGE,
    TrsakeyValueType,
)

__NAMESPACE__ = "http://www.portalfiscal.inf.br/cte"

"Tipo Modal transporte"
TMODTRANSP = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
]


class Tevento(models.AbstractModel):
    "Tipo Evento"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento"

    cte40_infEvento = fields.Many2one(
        comodel_name="cte.40.tevento_infevento",
        string="infEvento",
        xsd_required=True,
    )

    cte40_versao = fields.Char(
        string="versao", xsd_required=True, xsd_type="TVerEvento"
    )


class TeventoInfEvento(models.AbstractModel):
    _description = "infEvento"
    _name = "cte.40.tevento_infevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento.InfEvento"

    cte40_cOrgao = fields.Selection(
        TCORGAOIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        xsd_type="TCOrgaoIBGE",
        help=(
            "Código do órgão de recepção do Evento. Utilizar a Tabela do IBGE "
            "extendida, utilizar 90 para identificar SUFRAMA"
        ),
    )

    cte40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd_required=True,
        xsd_type="TAmb",
        help="Identificação do Ambiente:\n1 - Produção\n2 - Homologação",
    )

    cte40_CNPJ = fields.Char(
        string="CNPJ do emissor do evento",
        choice="infevento",
        xsd_choice_required=True,
        xsd_type="TCnpj",
    )

    cte40_CPF = fields.Char(
        string="CPF do emissor do evento",
        choice="infevento",
        xsd_choice_required=True,
        xsd_type="TCpf",
        help=(
            "CPF do emissor do evento\nInformar zeros não "
            "significativos.\n\nUsar com série específica 920-969 para "
            "emitente pessoa física com inscrição estadual"
        ),
    )

    cte40_chCTe = fields.Char(
        string="Chave de Acesso do CT-e vinculado",
        xsd_required=True,
        xsd_type="TChDFe",
        help="Chave de Acesso do CT-e vinculado ao evento",
    )

    cte40_dhEvento = fields.Datetime(
        string="Data e Hora do Evento",
        xsd_required=True,
        xsd_type="TDateTimeUTC",
        help="Data e Hora do Evento, formato UTC (AAAA-MM-DDThh:mm:ssTZD)",
    )

    cte40_tpEvento = fields.Char(string="Tipo do Evento", xsd_required=True)

    cte40_nSeqEvento = fields.Char(
        string="Seqüencial do evento para o mesmo tipo",
        xsd_required=True,
        help=(
            "Seqüencial do evento para o mesmo tipo de evento.  Para maioria "
            "dos eventos será 1, nos casos em que possa existir mais de um "
            "evento o autor do evento deve numerar de forma seqüencial."
        ),
    )

    cte40_detEvento = fields.Many2one(
        comodel_name="cte.40.detevento",
        string="Detalhamento do evento específico",
        xsd_required=True,
    )

    cte40_infSolicNFF = fields.Many2one(
        comodel_name="cte.40.tevento_infsolicnff",
        string="Grupo de informações do pedido",
        help=(
            "Grupo de informações do pedido de registro de evento da Nota "
            "Fiscal Fácil"
        ),
    )

    cte40_infPAA = fields.Many2one(
        comodel_name="cte.40.tevento_infpaa",
        string="Grupo de Informação do Provedor",
        help="Grupo de Informação do Provedor de Assinatura e Autorização",
    )

    cte40_Id = fields.Char(
        string="Identificador da TAG a ser assinada",
        xsd_required=True,
        help=(
            "Identificador da TAG a ser assinada, a regra de formação do Id "
            "é:\n“ID” + tpEvento +  chave do CT-e + nSeqEvento"
        ),
    )


class DetEvento(models.AbstractModel):
    "Detalhamento do evento específico"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.detevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento.InfEvento.DetEvento"

    cte40_versaoEvento = fields.Char(string="versaoEvento", xsd_required=True)


class TeventoInfSolicNff(models.AbstractModel):
    """Grupo de informações do pedido de registro de evento da Nota Fiscal
    Fácil"""

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tevento_infsolicnff"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento.InfEvento.InfSolicNff"

    cte40_xSolic = fields.Char(
        string="Solicitação do pedido de registro",
        xsd_required=True,
        help=(
            "Solicitação do pedido de registro de evento da NFF.\nSerá "
            "preenchido com a totalidade de campos informados no aplicativo "
            "emissor serializado."
        ),
    )


class TeventoInfPaa(models.AbstractModel):
    "Grupo de Informação do Provedor de Assinatura e Autorização"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tevento_infpaa"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento.InfEvento.InfPaa"

    cte40_CNPJPAA = fields.Char(
        string="CNPJ do Provedor de Assinatura",
        xsd_required=True,
        xsd_type="TCnpj",
        help="CNPJ do Provedor de Assinatura e Autorização",
    )

    cte40_PAASignature = fields.Many2one(
        comodel_name="cte.40.tevento_paasignature",
        string="Assinatura RSA do Emitente",
        xsd_required=True,
        help="Assinatura RSA do Emitente para DFe gerados por PAA",
    )


class TeventoPaasignature(models.AbstractModel):
    "Assinatura RSA do Emitente para DFe gerados por PAA"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tevento_paasignature"
    _inherit = "spec.mixin.cte"
    _binding_type = "Tevento.InfEvento.InfPaa.Paasignature"

    cte40_signatureValue = fields.Char(
        string="Assinatura digital padrão RSA",
        xsd_required=True,
        xsd_type="xs:base64Binary",
        help=(
            "Assinatura digital padrão RSA\nConverter o atributo Id do DFe "
            "para array de bytes e assinar com a chave privada do RSA com "
            "algoritmo SHA1 gerando um valor no formato base64."
        ),
    )

    cte40_RSAKeyValue = fields.Many2one(
        comodel_name="cte.40.trsakeyvaluetype",
        string="Chave Publica no padrão XML RSA Key",
        xsd_required=True,
        xsd_type="TRSAKeyValueType",
    )


class TretEvento(models.AbstractModel):
    "Tipo retorno do Evento"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tretevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "TretEvento"

    cte40_infEvento = fields.Many2one(
        comodel_name="cte.40.tretevento_infevento",
        string="infEvento",
        xsd_required=True,
    )

    cte40_versao = fields.Char(string="versao", xsd_required=True)


class TretEventoInfEvento(models.AbstractModel):
    _description = "infEvento"
    _name = "cte.40.tretevento_infevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "TretEvento.InfEvento"

    cte40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd_required=True,
        xsd_type="TAmb",
        help="Identificação do Ambiente:\n1 - Produção\n2 - Homologação",
    )

    cte40_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu",
        xsd_required=True,
        xsd_type="TVerAplic",
        help="Versão do Aplicativo que recebeu o Evento",
    )

    cte40_cOrgao = fields.Selection(
        TCORGAOIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        xsd_type="TCOrgaoIBGE",
        help=(
            "Código do órgão de recepção do Evento. Utilizar a Tabela do IBGE "
            "extendida, utilizar 90 para identificar SUFRAMA"
        ),
    )

    cte40_cStat = fields.Char(
        string="Código do status da registro do Evento",
        xsd_required=True,
        xsd_type="TStat",
    )

    cte40_xMotivo = fields.Char(
        string="Descrição literal do status do registro",
        xsd_required=True,
        xsd_type="TMotivo",
        help="Descrição literal do status do registro do Evento",
    )

    cte40_chCTe = fields.Char(
        string="Chave de Acesso CT-e vinculado", xsd_type="TChDFe"
    )

    cte40_tpEvento = fields.Char(string="Tipo do Evento vinculado")

    cte40_xEvento = fields.Char(string="Descrição do Evento")

    cte40_nSeqEvento = fields.Char(string="Seqüencial do evento")

    cte40_dhRegEvento = fields.Datetime(
        string="Data e Hora de do recebimento",
        xsd_type="TDateTimeUTC",
        help=(
            "Data e Hora de do recebimento do evento ou do registro do evento "
            "formato AAAA-MM-DDThh:mm:ssTZD"
        ),
    )

    cte40_nProt = fields.Char(
        string="Número do protocolo de registro",
        xsd_type="TProt",
        help="Número do protocolo de registro do evento",
    )

    cte40_Id = fields.Char(string="Id")


class TprocEvento(models.AbstractModel):
    "Tipo procEvento"

    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "cte.40.tprocevento"
    _inherit = "spec.mixin.cte"
    _binding_type = "TprocEvento"

    cte40_eventoCTe = fields.Many2one(
        comodel_name="cte.40.tevento",
        string="eventoCTe",
        xsd_required=True,
        xsd_type="TEvento",
    )

    cte40_retEventoCTe = fields.Many2one(
        comodel_name="cte.40.tretevento",
        string="retEventoCTe",
        xsd_required=True,
        xsd_type="TRetEvento",
    )

    cte40_versao = fields.Char(
        string="versao", xsd_required=True, xsd_type="TVerEvento"
    )

    cte40_ipTransmissor = fields.Char(
        string="IP do transmissor",
        xsd_type="TIPv4",
        help=(
            "IP do transmissor do documento fiscal para o ambiente autorizador"
        ),
    )

    cte40_nPortaCon = fields.Char(
        string="Porta de origem utilizada na conexão",
        help="Porta de origem utilizada na conexão (De 0 a 65535)",
    )

    cte40_dhConexao = fields.Datetime(
        string="Data e Hora da Conexão de Origem", xsd_type="TDateTimeUTC"
    )
