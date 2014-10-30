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
from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp

EUR = 351
THAI = 142


class hwf_monthly_report(osv.osv):
    
    _name = "hwf.monthly.report"
    _description = "Monthly Report Analysis"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'name': fields.char('Name', size=128, readonly=True),
        'date': fields.date('Effective Date', readonly=True),
        'date_created': fields.date('Date Created', readonly=True),
        'date_maturity': fields.date('Date Maturity', readonly=True),
        'ref': fields.char('Reference', size=64, readonly=True),
        'nbr': fields.integer('# of Items', readonly=True),
        'debit': fields.float('Debit', readonly=True),
        'credit': fields.float('Credit', readonly=True),
        'balance': fields.float('Balance', readonly=True),
        'debit_euro': fields.float('Debit (EURO)', readonly=True),
        'credit_euro': fields.float('Credit (EURO)', readonly=True),
        'balance_euro': fields.float('Balance (EURO)', readonly=True),
        'rate': fields.float('Rate (EURO)', readonly=True, group_operator="avg"),
        'day': fields.char('Day', size=128, readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'date': fields.date('Date', size=128, readonly=True),
        'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
        'amount_currency': fields.float('Amount Currency', digits_compute=dp.get_precision('Account'), readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month', readonly=True),
        'period_id': fields.many2one('account.period', 'Period', readonly=True),
        'account_id': fields.many2one('account.account', 'Account', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal', readonly=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_uom_id': fields.many2one('product.uom', 'Product Unit of Measure', readonly=True),
        'move_state': fields.selection([('draft','Unposted'), ('posted','Posted')], 'Status', readonly=True),
        'move_line_state': fields.selection([('draft','Unbalanced'), ('valid','Valid')], 'State of Move Line', readonly=True),
        'reconcile_id': fields.many2one('account.move.reconcile', readonly=True),
        'partner_id': fields.many2one('res.partner','Partner', readonly=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
        'quantity': fields.float('Products Quantity', digits=(16,2), readonly=True),
        'user_type': fields.many2one('account.account.type', 'Account Type', readonly=True),
        'type': fields.selection([
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('cash', 'Cash'),
            ('view', 'View'),
            ('consolidation', 'Consolidation'),
            ('other', 'Regular'),
            ('closed', 'Closed'),
        ], 'Internal Type', readonly=True, help="This type is used to differentiate types with "\
            "special effects in OpenERP: view can not have entries, consolidation are accounts that "\
            "can have children accounts for multi-company consolidations, payable/receivable are for "\
            "partners accounts (for debit/credit computations), closed for depreciated accounts."),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'statement_id': fields.many2one('account.bank.statement', 'Cash Register', readonly=True),
        'project_line_id': fields.many2one('npo.project.line', 'Project Line', readonly=True),
        'project_id': fields.many2one('npo.project', 'Project', readonly=True),
        'project_categ_id': fields.many2one('npo.project.categ', 'Project Category', readonly=True),
    }

    _order = 'date desc'
 
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        for arg in args:
            if arg[0] == 'period_id' and arg[2] == 'current_period':
                ctx = dict(context or {}, account_period_prefer_normal=True)
                current_period = period_obj.find(cr, uid, context=ctx)[0]
                args.append(['period_id','in',[current_period]])
                break
            elif arg[0] == 'period_id' and arg[2] == 'current_year':
                current_year = fiscalyear_obj.find(cr, uid)
                ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
                args.append(['period_id','in',ids])
        for a in [['period_id','in','current_year'], ['period_id','in','current_period']]:
            if a in args:
                args.remove(a)
        return super(hwf_monthly_report, self).search(cr, uid, args=args, offset=offset, limit=limit, order=order,
            context=context, count=count)
 
    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        if context is None:
            context = {}
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        if context.get('period', False) == 'current_period':
            ctx = dict(context, account_period_prefer_normal=True)
            current_period = period_obj.find(cr, uid, context=ctx)[0]
            domain.append(['period_id','in',[current_period]])
        elif context.get('year', False) == 'current_year':
            current_year = fiscalyear_obj.find(cr, uid)
            ids = fiscalyear_obj.read(cr, uid, [current_year], ['period_ids'])[0]['period_ids']
            domain.append(['period_id','in',ids])
        else:
            domain = domain
        return super(hwf_monthly_report, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'hwf_monthly_report')
        cr.execute("""
            create or replace view hwf_monthly_report as (
            select
                l.id as id,
                l.name,
                am.date as date,
                l.date_maturity as date_maturity,
                l.date_created as date_created,
                am.ref as ref,
                am.state as move_state,
                l.state as move_line_state,
                l.reconcile_id as reconcile_id,
                to_char(am.date, 'YYYY') as year,
                to_char(am.date, 'MM') as month,
                to_char(am.date, 'YYYY-MM-DD') as day,
                l.partner_id as partner_id,
                l.product_id as product_id,
                l.product_uom_id as product_uom_id,
                am.company_id as company_id,
                am.journal_id as journal_id,
                p.fiscalyear_id as fiscalyear_id,
                am.period_id as period_id,
                l.account_id as account_id,
                l.analytic_account_id as analytic_account_id,
                a.type as type,
                a.user_type as user_type,
                1 as nbr,
                l.quantity as quantity,
                l.currency_id as currency_id,
                l.amount_currency as amount_currency,
                l.debit as debit,
                l.credit as credit,
                l.debit-l.credit as balance,
                l.statement_id,
                l.debit / rate as debit_euro,
                l.credit / rate as credit_euro,
                (l.debit-l.credit) / rate as balance_euro,
                cr.rate,
                project_line_id,
                project_id,
                project_categ_id
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
                left join (select npl.account_id, npl.id project_line_id, np.id project_id, npc.id project_categ_id
                from npo_project_line npl join npo_project np on (npl.project_id = np.id)
                    join npo_project_categ npc on (np.project_categ_id = npc.id)) npo
                    ON (npo.account_id = l.account_id)
                JOIN res_currency_rate cr ON (cr.currency_id = %s)
                WHERE
                    cr.id IN (SELECT id
                          FROM res_currency_rate cr2
                          WHERE (cr2.currency_id = %s)
                          AND ((l.date IS NOT NULL AND cr2.name <= l.date)
                            OR (l.date IS NULL AND cr2.name <= NOW()))
                          ORDER BY name DESC LIMIT 1)               
                        and l.state != 'draft'
            )
        """ % (EUR, EUR))
hwf_monthly_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
