# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields, osv


class cash_register_item_report(osv.osv):

    _name = "cash.register.item.report"
    _description = "Cash Register Items Report"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'period_id': fields.many2one('account.period', 'Period'),
        'date': fields.date('Date'),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month': fields.selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
            ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')], 'Month', readonly=True),
        'cash_type':fields.selection([('cashin','In'),('cashout','Out')], 'In/Out'),
        'project_line_id': fields.many2one('npo.project.line', 'Line'),
        'obi_id': fields.many2one('npo.obi', 'Donor'),
        'name': fields.char('OBI', help="Originator to Beneficiary Information"),
        'obi_dest_id': fields.many2one('npo.obi', 'Rpt Donor'),
        'doc_number': fields.char('Ref#'),
        'project_categ_id': fields.many2one('npo.project.categ', 'Project Categ'),
        'project_id': fields.many2one('npo.project', 'Project'),
        'ref': fields.char('Reference'),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'type': fields.selection([
            ('supplier','Supplier'),
            ('customer','Customer'),
            ('general','General')
            ], 'Type'),
        'description': fields.char('Description'),
        'purpose': fields.char('Purpose'),
        'account_id': fields.many2one('account.account','Account'),
        'quantity': fields.float('Quantity'),
        'unit_price': fields.float('Unit Price'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'amount': fields.float('Amount'),
    }
    _order = 'date desc'

    def init(self, cr):
        # self._table = sale_invoice_payment_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW cash_register_item_report as (
            select head.period_id, line.id, line.date, line.cash_type, line.project_line_id, line.obi_id, line.name, line.obi_dest_id, line.doc_number, 
                line.project_categ_id, line.project_id, line.ref, line.partner_id, line.type, line.description, 
                line.purpose, line.account_id, line.quantity, line.unit_price, line.analytic_account_id, line.amount,
                to_char(line.date::timestamp with time zone, 'YYYY'::text) AS year,
                to_char(line.date::timestamp with time zone, 'MM'::text) AS month,
                to_char(line.date::timestamp with time zone, 'YYYY-MM-DD'::text) AS day
            from account_bank_statement_line line
                join account_bank_statement head on head.id = line.statement_id
        )""")

cash_register_item_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
