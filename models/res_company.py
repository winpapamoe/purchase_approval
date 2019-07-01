# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Company(models.Model):
    _inherit = 'res.company'

    manager_approval_max_amount = fields.Float(string='Max amount', default=100.0,
                                               help="Maximum amount for which manager approval is required")

    accountant_approval_max_amount = fields.Float(string='Max amount', default=1000.0,
                                                  help="Maximum amount for which Accountant approval is required")

    director_approval_min_amount = fields.Float(string='Min amount', default=1001.0,
                                                help="Minimum amount for which Director approval is required")
