from odoo import api, fields, models, _


class Coupon(models.Model):
    _inherit = 'coupon.coupon'

    order_id = fields.Many2one('sale.order', 'Order Reference', readonly=True,
        help="The sales order from which coupon is generated")
    sales_order_id = fields.Many2one('sale.order', 'Used in', readonly=True,
        help="The sales order on which the coupon is applied")

    def _check_coupon_code(self, order):
        message = {}
        applicable_programs = order._get_applicable_programs()
        if self.state == 'used':
            message = {'error': _('This coupon has already been used (%s).') % (self.code)}
        elif self.state == 'reserved':
            message = {'error': _('This coupon %s exists but the origin sales order is not validated yet.') % (self.code)}
        elif self.state == 'cancel':
            message = {'error': _('This coupon has been cancelled (%s).') % (self.code)}
        elif self.state == 'expired' or (self.expiration_date and self.expiration_date < fields.Datetime.now().date()):
            message = {'error': _('This coupon is expired (%s).') % (self.code)}
        # Minimum requirement should not be checked if the coupon got generated by a promotion program (the requirement should have only be checked to generate the coupon)
        elif self.program_id.program_type == 'coupon_program' and not self.program_id._filter_on_mimimum_amount(order):
            message = {'error': _(
                'A minimum of %(amount)s %(currency)s should be purchased to get the reward',
                amount=self.program_id.rule_minimum_amount,
                currency=self.program_id.currency_id.name
            )}
        elif not self.program_id.active:
            message = {'error': _('The coupon program for %s is in draft or closed state') % (self.code)}
        elif self.partner_id and self.partner_id != order.partner_id:
            message = {'error': _('Invalid partner.')}
        elif self.program_id in order.applied_coupon_ids.mapped('program_id'):
            message = {'error': _('A Coupon is already applied for the same reward')}
        elif self.program_id._is_global_discount_program() and order._is_global_discount_already_applied():
            message = {'error': _('Global discounts are not cumulable.')}
        elif self.program_id.reward_type == 'product' and not order._is_reward_in_order_lines(self.program_id):
            message = {'error': _('The reward products should be in the sales order lines to apply the discount.')}
        elif not self.program_id._is_valid_partner(order.partner_id):
            message = {'error': _("The customer doesn't have access to this reward.")}
        # Product requirement should not be checked if the coupon got generated by a promotion program (the requirement should have only be checked to generate the coupon)
        elif self.program_id.program_type == 'coupon_program' and not self.program_id._filter_programs_on_products(order):
            message = {'error': _("You don't have the required product quantities on your sales order. All the products should be recorded on the sales order. (Example: You need to have 3 T-shirts on your sales order if the promotion is 'Buy 2, Get 1 Free').")}
        else:
            if self.program_id not in applicable_programs and self.program_id.promo_applicability == 'on_current_order':
                message = {'error': _('At least one of the required conditions is not met to get the reward!')}
        return message
