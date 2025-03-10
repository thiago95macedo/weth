from odoo import models


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """ The widget 'timesheet_uom' needs to know which UoM conversion factor and which javascript
            widget to apply, depending on th ecurrent company.
        """
        result = super(Http, self).session_info()
        if self.env.user.has_group('base.group_user'):
            company = self.env.company
            encoding_uom = company.timesheet_encode_uom_id

            result['timesheet_uom'] = encoding_uom.read(['name', 'rounding', 'timesheet_widget'])[0]
            result['timesheet_uom_factor'] = company.project_time_mode_id._compute_quantity(1.0, encoding_uom, round=False)  # convert encoding uom into stored uom to get conversion factor
        return result
