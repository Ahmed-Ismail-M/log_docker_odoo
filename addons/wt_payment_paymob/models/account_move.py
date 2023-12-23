from odoo import api, fields, models
from odoo.addons.wt_payment_paymob.const import SUPPORTED_CURRENCIES

class AccountMove(models.Model):
    _inherit = "account.move"

    is_hide_paymob_button = fields.Boolean(string="is hide paymob Button", compute="_compute_is_check_enabled_for_backend_or_not")

    def get_invoice_details(self):
    	return {
    		'payment_option_id': self.env.ref('wt_payment_paymob.payment_acquirer_paymob').id,
    		'reference_prefix': self.name,
    		'amount': self.amount_residual,
    		'currency_id': self.currency_id.id if self.currency_id else False,
    		'partner_id': self.partner_id.id if self.partner_id else False,
    		'invoice_id': self.id,
    		'access_token': self._portal_ensure_token(),
    		'flow': 'redirect',
    		'tokenization_requested': False,
    		'landing_route': ''
    	}

    def _compute_is_check_enabled_for_backend_or_not(self):
    	for record in self:
	        rec = self.env.ref('wt_payment_paymob.payment_acquirer_paymob').sudo()
	        if rec.state in ['enabled', 'test'] and record.state == 'posted':
	        	if rec.is_backend_pay and record.currency_id and record.currency_id.name in SUPPORTED_CURRENCIES:
	        		record.is_hide_paymob_button = True
	        	else:
	        		record.is_hide_paymob_button = False
	        else:
	        	record.is_hide_paymob_button = False	
	        