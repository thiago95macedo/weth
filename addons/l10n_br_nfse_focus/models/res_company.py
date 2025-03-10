# Copyright 2023 - TODAY, KMEE INFORMATICA LTDA
# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escweth.com.br.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection_add=[
            ("focusnfe", "FocusNFe"),
        ]
    )

    focusnfe_production_token = fields.Char(
        string="FocusNFe Production Token",
    )

    focusnfe_homologation_token = fields.Char(
        string="FocusNFe Homologation Token",
    )

    focusnfe_nfse_service_type_value = fields.Selection(
        [
            ("item_lista_servico", "Service Type"),
            ("codigo_tributacao_municipio", "City Taxation Code"),
        ],
        string="NFSE Service Type Value",
        default="item_lista_servico",
    )

    focusnfe_nfse_cnae_code_value = fields.Selection(
        [
            ("codigo_cnae", "CNAE Code"),
            ("codigo_tributacao_municipio", "City Taxation Code"),
        ],
        string="NFSE CNAE Code Value",
        default="codigo_cnae",
    )

    focusnfe_nfse_update_authorized_document_status = fields.Boolean(
        string="Include Authorized Documents in Status Check",
        help="If checked, authorized documents will be included in the status check "
        "wizard. The system will verify the status of the documents with Focus NFE, "
        "and if there are discrepancies with the status in Odoo, it will automatically "
        "update the status in the system.",
        default=False,
    )

    focusnfe_nfse_force_odoo_danfse = fields.Boolean(
        string="Force WETH DANFSE",
        help="If checked, the system will always use the WETH DANFSE instead of the "
        "Focus DANFSE.",
        default=False,
    )

    def get_focusnfe_token(self):
        """
        Retrieve the appropriate FocusNFe API token based on the current NFSe
        environment setting.
        Decide between the production and homologation (test) environment tokens by
        examining the 'nfse_environment' field of the record.

        Precondition:
        - Call this method on a single record only. The method uses ensure_one to
        enforce this rule.

        Returns:
        - str: The FocusNFe token. Return the production token if 'nfse_environment'
        is set to "1"; otherwise, return the homologation token.

        Raises:
        - ValueError: If the method is called on a recordset containing more than one
        record.
        """
        self.ensure_one()
        return (
            self.focusnfe_production_token
            if self.nfse_environment == "1"
            else self.focusnfe_homologation_token
        )
