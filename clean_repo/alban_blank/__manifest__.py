{
    'name': 'Архив',
    'version': '16.0.1.0.0',
    'category': 'Tools',
    'summary': 'Албан бланкны загвар ба ашиглалт',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/mail_template_data.xml',
        'views/request_views.xml',
        'views/print_template_views.xml',
        'views/blank_usage_views.xml',
        'views/menu.xml',
        'reports/print_template_report.xml',
        'reports/print_template_qweb.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'alban_blank/static/src/css/style.css',
        ],
    },

    'installable': True,
    'application': True,
}
