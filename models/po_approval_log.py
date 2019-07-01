# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PoApprovalLog(models.Model):
    _name = 'po.approval.log'

    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    user_id = fields.Many2one('res.user', string='User')
    sender_email = fields.Char(string='Sender Email')
    receiver_email = fields.Char(string='Receiver Email')