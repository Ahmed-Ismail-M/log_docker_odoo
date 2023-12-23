# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models

from odoo.addons.wt_payment_paymob.const import SUPPORTED_CURRENCIES

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('paymob', "Paymob")], ondelete={'paymob': 'set default'})
    paymob_publishable_key = fields.Char(
        string="Publishable Key", help="The key solely used to identify the account with paymob",
        required_if_provider='paymob')
    paymob_secret_key = fields.Char(
        string="Secret Key", required_if_provider='paymob', groups='base.group_system')
    is_backend_pay = fields.Boolean(string="Backend Payment By Paymob");

    @api.onchange('state')
    def _onchange_auth_state(self):
        if self.provider == 'paymob':
            self.paymob_publishable_key = ''
            self.paymob_secret_key = ''

    @api.model
    def _get_compatible_acquirers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist Paymob acquirers when the currency is not supported. """
        acquirers = super()._get_compatible_acquirers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in SUPPORTED_CURRENCIES:
            acquirers = acquirers.filtered(lambda a: a.provider != 'paymob')

        return acquirers

    def _paymob_get_api_url(self):
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://flashapi.paymob.com/v1/intention/'
        else:
            return 'https://flashapi.paymob.com/v1/intention/'

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != 'paymob':
            return super()._get_default_payment_method_id()
        return self.env.ref('wt_payment_paymob.payment_method_paymob').id

    def paymob_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        values.update({
            "action_url": urls.url_join(base_url, '/payment/paymob/transction/process'),
        })
        return values