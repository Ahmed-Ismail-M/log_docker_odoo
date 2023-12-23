odoo.define('wt_payment_paymob.paymobwidget', function (require) {
    'use strict';
    var widgetRegistry = require('web.widget_registry');
    var Widget = require('web.Widget');
    var utils = require('web.utils');
    var core = require('web.core');
    var PaymobWidget = Widget.extend({
        template: 'wt_payment_paymob.paymob_button',
        xmlDependencies: ['/wt_payment_paymob/static/src/xml/paymobwidget.xml'],
        events: {
        'click .btn-primary': '_onClick'
        },
        init: function (parent, data, options) {
            this._super.apply(this, arguments);
            this.text = options.attrs.title || options.attrs.text;
            this.className = 'btn btn-primary';
            this.res_model = options.attrs.res_model || 'account.move';
        },
        willStart: function () {
            return Promise.all([
                this._super.apply(this, arguments),
            ]);
        },
        _prefill: function(){
            
        },
        _onClick: async function(){
            utils.set_cookie('paymob_reload_url', window.location.href);
            var self = this;
            var invoce_id = this.__parentedParent.state.data.id;
            const datas = await this._rpc({
                model: 'account.move',
                method: 'get_invoice_details',
                args: [invoce_id],
            });
            return this._rpc({
                route: '/paymob/payment/transaction/'+String(invoce_id),
                params: datas,
            }).then(processingValues => {
                processingValues['is_backend_pay'] = true;
                self.pay_by_payroc(processingValues);
            });
        },
        pay_by_payroc: function(processingValues){
            $.post('/payment/paymob/transction/process', processingValues).done(function(data, status ){
                var jsondata = JSON.parse(data);
                var sd = Paymob(jsondata.public_key).checkoutButton(jsondata.client_secret, { redirect: '/paymob/redirect/backend'}).mount("#paymob-checkout");
                $('body').unblock();
                $("#paymob-checkout > button").first().click();
            }).fail(function(xhr, status, error) {
                $('body').unblock();
                self.alert(xhr.responseText);
            });
            return;
        }
    });

    widgetRegistry.add('paymob_button', PaymobWidget);

    return PaymobWidget;
});
