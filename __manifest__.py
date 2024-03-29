# -*- coding: utf-8 -*-

{
    'name': 'Open HRMS Leave Multi-Level Approval   ',
    'version': '13.0.1.1.0',
    'summary': """Multilevel Approval for Leaves""",
    'description': 'Multilevel Approval for Leaves, leave approval, multiple leave approvers, leave, approval',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['base_setup', 'hr_holidays'],
    'data': [
        'wizards/create_leave_comment.xml',
        'wizards/create_refuse_comment.xml',
        'views/leave_request_test.xml',
        'data/mail_template.xml',
        # 'views/leave_request.xml',
        'security/ir.model.access.csv',
        'security/security.xml'
    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
