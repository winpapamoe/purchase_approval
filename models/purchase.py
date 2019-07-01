# -*- coding: utf-8 -*-

import logging
import odoo.tools
import base64
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('manager_approval', 'Waiting Purchase Manager Approval'),
        ('accountant_approval', 'Waiting Accountant Approval'),
        ('director_approval', 'Waiting Director Approval'),
        ('approved', 'Approved'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    button_control = fields.Boolean(compute='_check_button_disable', string='Button Control')

    # override method for approval process
    @api.model
    def create(self, vals):
        vals['state'] = 'manager_approval'
        res = super(PurchaseOrder, self).create(vals)
        # Getting Email List #
        group_id = self.env['ir.model.data'].xmlid_to_res_id('purchase.group_purchase_manager')
        email_list = self.get_users_email_from_group(group_id)
        res._send_mail(email_list)
        return res

    @api.multi
    def _send_mail(self, receiver_email):
        template_id = self.env['ir.model.data'].get_object_reference('purchase_approval',
                                                                     'email_template_purchase_approval')[1]
        template_browse = self.env['mail.template'].browse(template_id)
        if template_browse:
            values = template_browse.generate_email(self.id, fields=None)
            values['email_to'] = receiver_email
            values['email_from'] = self.env.user.partner_id.email
            values['res_id'] = False
            if not values['email_to'] and not values['email_from']:
                pass
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.sudo().create(values)
            if msg_id:
                msg_id.send(True)
                self.approval_send_mail_log(self.env.user.partner_id.email, receiver_email)
            return True

    @api.multi
    def approval_send_mail_log(self, sender, receiver):
        vals = {
            'purchase_id': self.id,
            'user_id': self.env.user.id,
            'sender_email': sender,
            'receiver_email': receiver
        }

        self.env['po.approval.log'].create(vals)
        return True

    # passing group id using self.env['ir.model.data'].xmlid_to_res_id('purchase.group_purchase_manager')
    @api.multi
    def get_users_email_from_group(self, group_id):
        users_email = ""
        sql_query = """select id from res_users where id in 
                    (select uid from res_groups_users_rel where gid = %s) and active=True"""
        params = (group_id,)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.fetchall()
        for users_id in results:
            users_email += self.env['res.users'].browse(users_id[0]).partner_id.email + ","
        return users_email

    @api.multi
    def button_manager_approve(self):
        if self.amount_total > self.company_id.manager_approval_max_amount:
            self.write({'state': 'accountant_approval'})
            group_id = self.env['ir.model.data'].xmlid_to_res_id('account.group_account_manager')
            email_list = self.get_users_email_from_group(group_id)
            self._send_mail(email_list)
        else:
            self.write({'state': 'approved'})
        return True

    @api.multi
    def button_accountant_approve(self):
        if self.amount_total > self.company_id.accountant_approval_max_amount:
            self.write({'state': 'director_approval'})
            group_id = self.env['ir.model.data'].xmlid_to_res_id('purchase_approval.group_hr_director')
            email_list = self.get_users_email_from_group(group_id)
            self._send_mail(email_list)
        else:
            self.write({'state': 'approved'})
        return True

    @api.multi
    def button_director_approve(self):
        self.write({'state': 'approved'})
        return True

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'approved']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id.compute(
                        order.company_id.po_double_validation_amount, order.currency_id)) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def _check_button_disable(self):
        if self.env.user.has_group('purchase.group_purchase_manager') and self.state != "manager_approval":
            self.button_control = True
        elif self.env.user.has_group('account.group_account_user') and self.state != "accountant_approval":
            if (self.amount_total > self.company_id.manager_approval_max_amount) \
                    and self.amount_total < self.company_id.accountant_approval_max_amount:
                self.button_control = True
            elif self.amount_total > self.company_id.accountant_approval_max_amount:
                self.button_control = True
            else:
                self.button_control = False
        elif self.env.user.has_group('purchase_approval.group_hr_director') \
                and self.amount_total > self.company_id.accountant_approval_max_amount and self.state == "approved":
            self.button_control = True
        else:
            self.button_control = False


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    manager_approval_max_amount = fields.Float(related='company_id.manager_approval_max_amount',
                                               string="Maximum Amount for Manager",
                                               currency_field='company_currency_id')
    accountant_approval_max_amount = fields.Float(related='company_id.accountant_approval_max_amount',
                                               string="Maximum Amount for Accountant",
                                               currency_field='company_currency_id')
    director_approval_min_amount = fields.Float(related='company_id.director_approval_min_amount',
                                                  string="Minimum Amount for Director", currency_field='company_currency_id')
