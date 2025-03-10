# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escweth.com.br.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _cte_search_keys = ["ibge_code", "code"]
    _cte_extra_domain = [("ibge_code", "!=", False)]

    @api.model
    def match_or_create_m2o(self, rec_dict, parent_dict, model=None):
        """If state not found, break hard, don't create it"""

        if rec_dict.get("code"):
            domain = [("code", "=", rec_dict.get("code")), ("ibge_code", "!=", False)]
            match = self.search(domain, limit=1)
            if match:
                return match.id
        return False
