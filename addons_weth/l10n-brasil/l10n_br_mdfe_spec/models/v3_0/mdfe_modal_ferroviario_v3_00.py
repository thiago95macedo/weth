# Copyright 2023 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated by https://github.com/akretion/xsdata-odoo
#
import textwrap
from odoo import fields, models

__NAMESPACE__ = "http://www.portalfiscal.inf.br/mdfe"


class Ferrov(models.AbstractModel):
    "Informações do modal Ferroviário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "mdfe.30.ferrov"
    _inherit = "spec.mixin.mdfe"
    _binding_type = "Ferrov"

    mdfe30_trem = fields.Many2one(
        comodel_name="mdfe.30.trem",
        string="Informações da composição do trem",
        xsd_required=True,
    )

    mdfe30_vag = fields.One2many(
        "mdfe.30.vag", "mdfe30_vag_ferrov_id", string="informações dos Vagões"
    )


class Trem(models.AbstractModel):
    "Informações da composição do trem"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "mdfe.30.trem"
    _inherit = "spec.mixin.mdfe"
    _binding_type = "Ferrov.Trem"

    mdfe30_xPref = fields.Char(string="Prefixo do Trem", xsd_required=True)

    mdfe30_dhTrem = fields.Datetime(
        string="Data e hora de liberação do trem",
        xsd_type="TDateTimeUTC",
        help="Data e hora de liberação do trem na origem",
    )

    mdfe30_xOri = fields.Char(
        string="Origem do Trem",
        xsd_required=True,
        help="Origem do Trem\nSigla da estação de origem",
    )

    mdfe30_xDest = fields.Char(
        string="Destino do Trem",
        xsd_required=True,
        help="Destino do Trem\nSigla da estação de destino",
    )

    mdfe30_qVag = fields.Char(
        string="Quantidade de vagões carregados", xsd_required=True
    )


class Vag(models.AbstractModel):
    "informações dos Vagões"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = "mdfe.30.vag"
    _inherit = "spec.mixin.mdfe"
    _binding_type = "Ferrov.Vag"

    mdfe30_vag_ferrov_id = fields.Many2one(
        comodel_name="mdfe.30.ferrov", xsd_implicit=True, ondelete="cascade"
    )
    mdfe30_pesoBC = fields.Float(
        string="Peso Base de Cálculo de Frete",
        xsd_required=True,
        xsd_type="TDec_0303",
        digits=(
            3,
            3,
        ),
        help="Peso Base de Cálculo de Frete em Toneladas",
    )

    mdfe30_pesoR = fields.Float(
        string="Peso Real em Toneladas",
        xsd_required=True,
        xsd_type="TDec_0303",
        digits=(
            3,
            3,
        ),
    )

    mdfe30_tpVag = fields.Char(string="Tipo de Vagão")

    mdfe30_serie = fields.Char(
        string="Serie de Identificação do vagão", xsd_required=True
    )

    mdfe30_nVag = fields.Char(
        string="Número de Identificação do vagão", xsd_required=True
    )

    mdfe30_nSeq = fields.Char(string="Sequencia do vagão na composição")

    mdfe30_TU = fields.Char(
        string="Tonelada Útil",
        xsd_required=True,
        help=(
            "Tonelada Útil\nUnidade de peso referente à carga útil (apenas o "
            "peso da carga transportada), expressa em toneladas."
        ),
    )
