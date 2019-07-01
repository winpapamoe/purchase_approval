# -*- coding: utf-8 -*-


{
    'name': 'Purchase Order Approval',
    'version': '1.0',
    'category': '',
    'description': """
        This module provides facility to the user to request approval from manager, 
        accounts and director depends on purchase amount.
    """,
    'website': '',
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_security.xml',
        'views/purchase_config_inherit.xml',
        'views/purchase_view.xml',
        'views/css_template.xml',
        'views/email_template.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
