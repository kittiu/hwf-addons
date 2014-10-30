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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

EUR = 351
THAI = 142

class account_bank_statement(osv.osv):

#     def _get_last_conversion_rate(self, cr, uid, *args):
#         cr.execute('select conversion_rate from account_bank_statement order by id desc limit 1')
#         res = cr.fetchone()
#         return res and res[0] or 0.0
    
    def _get_current_conversion_rate(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context):
            euro = self.pool.get('res.currency').browse(cr, uid, EUR)  # EUR
            thai = self.pool.get('res.currency').browse(cr, uid, THAI)  # THAI
            c = context.copy()
            c.update({'date': obj.date})
            rate = self.pool.get('res.currency')._get_conversion_rate(cr, uid, euro, thai, c)
            res[obj.id] = rate
        return res
    
    _inherit = 'account.bank.statement'
    _columns = {   
        'conversion_rate': fields.function(_get_current_conversion_rate, type='float', string='Conversion Rate (EURO)', digits_compute=dp.get_precision('Account')),
        #'conversion_rate': fields.float('Conversion Rate (EURO)', digits_compute=dp.get_precision('Account')),
        'line_cashin_ids': fields.one2many('account.bank.statement.line',
            'statement_id', 'Statement lines',
            domain=[('cash_type','=','cashin')],
            states={'confirm':[('readonly', True)]}),    
        'line_cashout_ids': fields.one2many('account.bank.statement.line',
            'statement_id', 'Statement lines',
            domain=[('cash_type','=','cashout')],
            states={'confirm':[('readonly', True)]}),        
    }
    _defaults = {
        #'conversion_rate': _get_current_conversion_rate,
    }
    
  
account_bank_statement()

class account_bank_statement_line(osv.osv):
    
    def _get_cash_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('default_cashtype', 'cashin')
    
    def _get_next_doc_number(self, cr, uid, context=None):
        if context is None:
            context = {}
        active_id = context.get('active_id', False)
        res = False
        if active_id:
            cr.execute("select coalesce(max(doc_number)+1,1) as next_doc_number \
                            from account_bank_statement b \
                            left outer join account_bank_statement_line bl on b.id = bl.statement_id \
                            where b.id = %s",
                           (active_id,))
            res = cr.fetchone()[0]
        return res
     
    _inherit = 'account.bank.statement.line'
    _columns = {
        'name': fields.char('OBI', required=False, help="Originator to Beneficiary Information"),
        'cash_type':fields.selection([('cashin','In'),('cashout','Out')], 'In/Out'),
        'obi_id': fields.many2one('npo.obi', 'Donor', required=False),
        'obi_dest_id': fields.many2one('npo.obi', 'Rpt Donor', required=False),
        'doc_number': fields.char('Ref#', required=False),
        'project_categ_id': fields.many2one('npo.project.categ', 'Project Categ', required=False),
        'project_id': fields.many2one('npo.project', 'Project', domain="[('project_categ_id','=',project_categ_id)]", required=False),
        'project_line_id': fields.many2one('npo.project.line', 'Line', required=False),
        'description': fields.char('Description', size=256, required=True),
        'purpose': fields.char('Purpose', size=256),
        'quantity': fields.float('Quantity'),
        'unit_price': fields.float('Unit Price'),
    }
    _defaults = {
        'cash_type': _get_cash_type,
        #'doc_number': _get_next_doc_number,
        'quantity': 1.0,
        'unit_price': 0.0,
    }
    _order = 'id'
    
    def onchange_project_line_id(self, cr, uid, ids, project_line_id, account_id, context=None):
        if context is None:
            context = {}
        if not project_line_id and not account_id:
            return {}
        obj = self.pool.get('npo.project.line')
        # Case 1: If choose project_line, assign account and other info.
        if project_line_id and not account_id:
            project_line = obj.browse(cr, uid, project_line_id, context=context)
            obi_ids = [x.obi_id.id for x in project_line.budget_line]
            return {'domain': {'obi_id': [('id', 'in', obi_ids)]},
                    'value': {'account_id': project_line.account_id and project_line.account_id.id or False,
                              'project_id': project_line.project_id and project_line.project_id.id or False,
                              'project_categ_id': project_line.project_id and project_line.project_id.project_categ_id.id or False,
                              'obi_id': obi_ids and obi_ids[0] or False,
                              }}
        # Case 2: If choose account_id, get the first project line, then get other info
        if account_id and not project_line_id:
            line_ids = obj.search(cr, uid, [('account_id', '=', account_id)])
            if line_ids:
                project_line_id = line_ids[0]
                project_line = obj.browse(cr, uid, line_ids[0], context=context)
                obi_ids = [x.obi_id.id for x in project_line.budget_line]
                return {'domain': {'obi_id': [('id', 'in', obi_ids)]},
                        'value': {'project_line_id': project_line_id or False,
                                  'project_id': project_line.project_id and project_line.project_id.id or False,
                                  'project_categ_id': project_line.project_id and project_line.project_id.project_categ_id.id or False,
                                  'obi_id': obi_ids and obi_ids[0] or False,
                                  }}
        return {'value': {}}        
        
    def onchange_obi_id(self, cr, uid, ids, obi_id, description, context=None):
        if context is None:
            context = {}
        if not obi_id:
            return {'value': {'name': description}}
        obj_obi = self.pool.get('npo.obi')
        obi = obj_obi.browse(cr, uid, obi_id, context=context)
        return {'value': {'name': obi.name}}
    
    def onchange_qty_price(self, cr, uid, ids, cash_type, quantity, unit_price, context=None):
        if context is None:
            context = {}
        quantity = quantity or 0.0
        unit_price = unit_price or 0.0
        amount = quantity * unit_price * (cash_type == 'cashin' and 1 or -1)
        return {'value': {'amount': amount}}
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('cash_type', 'cashin') == 'cashout':
            vals['amount'] = - abs(vals['amount']) # Always keep as negative
        else:
            vals['amount'] = abs(vals['amount']) # Always keep as positive
        return super(account_bank_statement_line, self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('amount', False) and (self.browse(cr, uid, ids[0]).cash_type or 'cashin') == 'cashout':
            vals['amount'] = - abs(vals['amount'])
            return super(account_bank_statement_line, self).write(cr, uid, ids[0], vals, context=context)
        elif vals.get('amount', False):
            vals['amount'] = abs(vals['amount'])
            return super(account_bank_statement_line, self).write(cr, uid, ids[0], vals, context=context)
        else:
            return super(account_bank_statement_line, self).write(cr, uid, ids, vals, context=context)
    
account_bank_statement_line()
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
