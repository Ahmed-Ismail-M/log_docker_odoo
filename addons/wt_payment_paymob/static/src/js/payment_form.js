odoo.define('wt_payment_paymob.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const ajax = require('web.ajax');

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const _t = core._t;

    const PaymobMixin = {
        _processRedirectPayment: function (provider, paymentOptionId, processingValues) {
            if (provider !== 'paymob') {
                return this._super(...arguments);
            }
            var self = this;
            $.post('/payment/paymob/transction/process', processingValues).done(function(data, status ){
                var jsondata = JSON.parse(data);
                var sd = Paymob(jsondata.public_key).checkoutButton(jsondata.client_secret, {redirect: "/payment/status"}).mount("#paymob-checkout");
                $('body').unblock();
                $("#paymob-checkout > button").first().click();
            }).fail(function(xhr, status, error) {
                $('body').unblock();
                self._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    xhr.responseText
                );
            })
            return;
        },
    };

    checkoutForm.include(PaymobMixin);
    manageForm.include(PaymobMixin);
});