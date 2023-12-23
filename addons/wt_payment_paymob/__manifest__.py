# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Paymob Payment Acquirer',
    'version': '1.0',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 100,
    'summary': 'Payment Acquirer: Paymob Implementation',
    'description': """Paymob Payment Acquirer""",
    'author': "Paymob",
    'website': "http://paymob.com",
    'support': "support@warlocktechnologies.com",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_paymob_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/images/screen_image.png'],
    'application': True,
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'wt_payment_paymob/static/src/js/payment_form.js',
        ],
        'web.assets_backend': [
            'wt_payment_paymob/static/src/scss/backend.scss',
            'https://flashjs.paymob.com/v1/paymob.js',
            'wt_payment_paymob/static/src/js/paymobwidget.js',
        ]
    },
    'license': 'LGPL-3',
}
