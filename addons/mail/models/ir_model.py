from odoo import _, api, fields, models
from odoo.exceptions import UserError


class Base(models.AbstractModel):
    _inherit = 'base'

    def _valid_field_parameter(self, field, name):
        # allow tracking on abstract models; see also 'mail.thread'
        return (
            name == 'tracking' and self._abstract
            or super()._valid_field_parameter(field, name)
        )


class IrModel(models.Model):
    _inherit = 'ir.model'
    _order = 'is_mail_thread DESC, name ASC'

    is_mail_thread = fields.Boolean(
        string="Mail Thread", default=False,
        help="Whether this model supports messages and notifications.",
    )
    is_mail_activity = fields.Boolean(
        string="Mail Activity", default=False,
        help="Whether this model supports activities.",
    )
    is_mail_blacklist = fields.Boolean(
        string="Mail Blacklist", default=False,
        help="Whether this model supports blacklist.",
    )

    def unlink(self):
        # Delete followers, messages and attachments for models that will be unlinked.
        models = tuple(self.mapped('model'))

        query = "DELETE FROM mail_followers WHERE res_model IN %s"
        self.env.cr.execute(query, [models])

        query = "DELETE FROM mail_message WHERE model in %s"
        self.env.cr.execute(query, [models])

        # Get files attached solely by the models
        query = """
            SELECT DISTINCT store_fname
            FROM ir_attachment
            WHERE res_model IN %s
            EXCEPT
            SELECT store_fname
            FROM ir_attachment
            WHERE res_model not IN %s;
        """
        self.env.cr.execute(query, [models, models])
        fnames = self.env.cr.fetchall()

        query = """DELETE FROM ir_attachment WHERE res_model in %s"""
        self.env.cr.execute(query, [models])

        for (fname,) in fnames:
            self.env['ir.attachment']._file_delete(fname)

        return super(IrModel, self).unlink()

    def write(self, vals):
        if self and ('is_mail_thread' in vals or 'is_mail_activity' in vals or 'is_mail_blacklist' in vals):
            if any(rec.state != 'manual' for rec in self):
                raise UserError(_('Only custom models can be modified.'))
            if 'is_mail_thread' in vals and any(rec.is_mail_thread > vals['is_mail_thread'] for rec in self):
                raise UserError(_('Field "Mail Thread" cannot be changed to "False".'))
            if 'is_mail_activity' in vals and any(rec.is_mail_activity > vals['is_mail_activity'] for rec in self):
                raise UserError(_('Field "Mail Activity" cannot be changed to "False".'))
            if 'is_mail_blacklist' in vals and any(rec.is_mail_blacklist > vals['is_mail_blacklist'] for rec in self):
                raise UserError(_('Field "Mail Blacklist" cannot be changed to "False".'))
            res = super(IrModel, self).write(vals)
            self.flush()
            # setup models; this reloads custom models in registry
            self.pool.setup_models(self._cr)
            # update database schema of models
            models = self.pool.descendants(self.mapped('model'), '_inherits')
            self.pool.init_models(self._cr, models, dict(self._context, update_custom_fields=True))
        else:
            res = super(IrModel, self).write(vals)
        return res

    def _reflect_model_params(self, model):
        vals = super(IrModel, self)._reflect_model_params(model)
        vals['is_mail_thread'] = isinstance(model, self.pool['mail.thread'])
        vals['is_mail_activity'] = isinstance(model, self.pool['mail.activity.mixin'])
        vals['is_mail_blacklist'] = isinstance(model, self.pool['mail.thread.blacklist'])
        return vals

    @api.model
    def _instanciate(self, model_data):
        model_class = super(IrModel, self)._instanciate(model_data)
        if model_data.get('is_mail_blacklist') and model_class._name != 'mail.thread.blacklist':
            parents = model_class._inherit or []
            parents = [parents] if isinstance(parents, str) else parents
            model_class._inherit = parents + ['mail.thread.blacklist']
            if model_class._custom:
                model_class._primary_email = 'x_email'
        elif model_data.get('is_mail_thread') and model_class._name != 'mail.thread':
            parents = model_class._inherit or []
            parents = [parents] if isinstance(parents, str) else parents
            model_class._inherit = parents + ['mail.thread']
        if model_data.get('is_mail_activity') and model_class._name != 'mail.activity.mixin':
            parents = model_class._inherit or []
            parents = [parents] if isinstance(parents, str) else parents
            model_class._inherit = parents + ['mail.activity.mixin']
        return model_class
