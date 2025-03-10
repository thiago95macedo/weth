from odoo import models, api, _
from odoo.exceptions import UserError

from odoo.tools import float_compare


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def retrieve_attachment(self, record):
        # get the original bills through the message_main_attachment_id field of the record
        if self.report_name == 'account.report_original_vendor_bill' and record.message_main_attachment_id:
            if record.message_main_attachment_id.mimetype == 'application/pdf' or \
               record.message_main_attachment_id.mimetype.startswith('image'):
                return record.message_main_attachment_id
        return super(IrActionsReport, self).retrieve_attachment(record)

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        # don't include the generated dummy report
        if self.report_name == 'account.report_original_vendor_bill':
            pdf_content = None
            res_ids = None
            if not save_in_attachment:
                raise UserError(_("No original vendor bills could be found for any of the selected vendor bills."))
        return super(IrActionsReport, self)._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

    def _postprocess_pdf_report(self, record, buffer):
        # don't save the 'account.report_original_vendor_bill' report as it's just a mean to print existing attachments
        if self.report_name == 'account.report_original_vendor_bill':
            return None
        res = super(IrActionsReport, self)._postprocess_pdf_report(record, buffer)
        if self.model == 'account.move' and record.state == 'posted' and record.is_sale_document(include_receipts=True):
            attachment = self.retrieve_attachment(record)
            if attachment:
                attachment.register_as_main_attachment(force=False)
        return res

    def _render_qweb_pdf(self, res_ids=None, data=None):
        # Overridden so that the print > invoices actions raises an error
        # when trying to print a miscellaneous operation instead of an invoice.
        # + append context data with the display_name_in_footer parameter
        if self.model == 'account.move' and res_ids:
            invoice_reports = (self.env.ref('account.account_invoices_without_payment'), self.env.ref('account.account_invoices'))
            if self in invoice_reports:
                if self.env['ir.config_parameter'].sudo().get_param('account.display_name_in_footer'):
                    data = data and dict(data) or {}
                    data.update({'display_name_in_footer': True})
                moves = self.env['account.move'].browse(res_ids)
                if any(not move.is_invoice(include_receipts=True) for move in moves):
                    raise UserError(_("Only invoices could be printed."))

        return super()._render_qweb_pdf(res_ids=res_ids, data=data)

    def _get_rendering_context(self, docids, data):
        data = data and dict(data) or {}
        data.update({'float_compare': float_compare})
        return super()._get_rendering_context(docids=docids, data=data)
