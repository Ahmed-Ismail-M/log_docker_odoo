# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.wt_payment_paymob.controllers.main import PaymobController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    paymob_payment_ref = fields.Char(string="Paymob Payment Reference")

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """ Override of payment to find the transaction based on Paypal data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'paymob':
            return tx
        try:
            tx_id = data['intention']['extras']['creation_extras']['tx_id']
            tx = self.search([('id', '=', int(tx_id)), ('provider', '=', 'paymob')])
            if not tx:
                raise ValidationError(
                    "Paymob: " + _("No transaction found")
                )
        except Exception as e:
            raise ValidationError(
                    "Paymob: " + _("No transaction found")
                )
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on Paymob data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_feedback_data(data)
        if self.provider != 'paymob':
            return
        if data:
            for status in data['intention']['transactions']:
                if status['status'] == "Success" \
                    and status['is_voided'] == False \
                    and status['is_refunded'] == False \
                    and status['is_captured'] == False:
                    self.paymob_payment_ref = status['payment_reference']
                    self._set_done()
                    if data['is_backend_pay']:
                        self._finalize_post_processing()
                elif status['is_voided'] == True \
                    and status['is_refunded'] == False \
                    and status['is_captured'] == False:
                    self._set_canceled()
                else:
                    self._set_error(
                        "Paymob: " + _(
                            "%(error)s)",
                            error='Your Payment not Successfully paid'
                        )
                    )
        else:
            self._set_error(
                "Payroc: " + _(
                    "%(error)s)",
                    error='Your Payment not Successfully paid'
                )
            )