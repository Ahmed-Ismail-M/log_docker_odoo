# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from odoo.fields import Command
import requests
from requests.exceptions import ConnectionError, HTTPError
from werkzeug import urls

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request, Response
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

import json
_logger = logging.getLogger(__name__)

class PaymentPortal(payment_portal.PaymentPortal):

    @http.route(
        '/paymob/payment/transaction/<int:invoice_id>', type='json', auth='public', website=True
    )
    def paymob_payment_transaction(self, invoice_id, access_token, **kwargs):
        """ Create a draft transaction and return its processing values.

        :param int order_id: The sales order to pay, as a `sale.order` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """
        # Check the order id and the access token
        try:
            self._document_check_access('account.move', invoice_id, access_token)
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError("The access token is invalid.")

        kwargs.pop('custom_create_values', None)  # Don't allow passing arbitrary create values
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set([invoice_id])]}, **kwargs,
        )

        # Store the new transaction into the transaction list and if there's an old one, we remove
        # it until the day the ecommerce supports multiple orders at the same time.
        last_tx_id = request.session.get('__backend_payment_last_tx_id')
        last_tx = request.env['payment.transaction'].browse(last_tx_id).sudo().exists()
        if last_tx:
            PaymentPostProcessing.remove_transactions(last_tx)
        request.session['__backend_payment_last_tx_id'] = tx_sudo.id

        return tx_sudo._get_processing_values()

    @http.route(
        '/paymob/redirect/backend', type='http', auth='public', website=True
    )
    def paymob_backend_redirec(self):
        return request.redirect(request.httprequest.cookies.get('paymob_reload_url'))

class PaymobController(http.Controller):
    _return_url = '/api/acceptance/post_pay'
    @http.route([_return_url], type="http", auth='public', methods=['GET', 'POST'], csrf=False)
    def paymob_transction_response(self, **kw):
        resdatas = json.loads(request.httprequest.data)
        if resdatas['intention'] and resdatas['intention']['extras'] and \
            resdatas['intention']['extras']['creation_extras'] and \
            resdatas['intention']['extras']['creation_extras']['is_backend_pay'] == 'true':
                resdatas['is_backend_pay'] = True
        else:
            resdatas['is_backend_pay'] = False
        request.env['payment.transaction'].sudo()._handle_feedback_data('paymob', resdatas)
        return request.redirect('/payment/status')

    @http.route('/payment/paymob/transction/process', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def paymob_transction_process(self, **data):
        _logger.info("beginning DPN with post data:\n%s", pprint.pformat(data))
        try:
            if not data.get('reference'):
                raise ValidationError("Paymob: " + _("Transaction not Created"))
            tx_sudo = request.env['payment.transaction'].sudo().search([('reference', '=', data.get('reference'))])
            acquirer_sudo = request.env['payment.acquirer'].sudo().search([('id', '=', int(data.get('acquirer_id')))])

            res = self.paymob_create_indention(tx_sudo, acquirer_sudo , **data)
            if res.status_code != 201:
                raise Exception("Paymob: " + _(res.text))
            conres = self.confirm_indention_paymob(tx_sudo, acquirer_sudo, **json.loads(res.text))
            if res.status_code != 201:
                raise Exception("Paymob: " + _(res.text))
            datas = json.loads(conres.text)
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            datas['return_url'] =  urls.url_join(base_url,'/sk/api/acceptance/post_pay')
            datas['public_key'] = acquirer_sudo.paymob_publishable_key
            return json.dumps(datas)
        except Exception as e:
            return Response(str(e), status=500)

    def paymob_create_indention(self, tx_id=None, acquirer_sudo=None, **data):
        url = "https://flashapi.paymob.com/v1/intention/" 
        payload = {
            "amount": str(int(float(data.get('amount')) * 100)),
            "currency": "EGP",
            "payment_methods": ["card"],
            "billing_data": {
                "apartment": "NA",
                "email": tx_id.partner_id.email,
                "floor": "NA",
                "first_name": tx_id.partner_id.name,
                "street": tx_id.partner_id.street,
                "building": "NA",
                "phone_number": tx_id.partner_id.phone.replace(' ',''),
                "shipping_method": "PKG",
                "postal_code": tx_id.partner_id.zip,
                "city": tx_id.partner_id.city,
                "country": tx_id.partner_id.country_id.code if tx_id.partner_id.country_id else "",
                "last_name": tx_id.partner_id.name,
                "state": tx_id.partner_id.state_id.name if tx_id.partner_id.state_id else ''
            },
            "customer": {
                "first_name": tx_id.partner_id.name,
                "last_name": tx_id.partner_id.name,
                "email": tx_id.partner_id.email
            },
            "items": [
                {
                    "name": data.get('reference'),
                    "amount": str(int(float(data.get('amount')) * 100)),
                    "description": "order desc",
                    "quantity": "1"
                }
            ],
            "extras": {"tx_id": str(tx_id.id), "is_backend_pay": data.get('is_backend_pay', False)}
        }
        headers = {
            "Accept": "application/json",
            "Authorization": "Token %s" %(acquirer_sudo.paymob_secret_key),
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response

    def confirm_indention_paymob(self, tx_id=None, acquirer_sudo=None, **data):
        url = "https://flashapi.paymob.com/v1/intention/%s" %(data.get('id'))
        headers = {
            "Accept": "application/json",
            "Authorization": "Token %s" %(acquirer_sudo.paymob_secret_key)
        }
        response = requests.get(url, headers=headers) 
        return response