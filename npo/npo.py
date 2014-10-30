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

from openerp.osv import osv, fields


class npo_obi(osv.osv):
    _name = 'npo.obi'
    _description = 'Originator to Beneficiary Information'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'description': fields.char('Description', size=256, required=False),
        'active': fields.boolean('Active'), 
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The name of this OBI must be unique !"),
    ]
npo_obi()

# kittiu: Description is change to be Char
# class npo_cash_desc(osv.osv):
#     _name = 'npo.cash.desc'
#     _description = 'Description for cash transaction'
#     _columns = {
#         'name': fields.char('Name', size=128, required=True),
#         'active': fields.boolean('Active'), 
#     }
#     _defaults = {
#         'active': True,
#     }
#     _sql_constraints = [
#         ('uniq_name', 'unique(name)', "The cash description must be unique!"),
#     ]
# npo_cash_desc()


class npo_project_categ(osv.osv):
    _name = 'npo.project.categ'
    _description = 'Project Category'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'description': fields.char('Description', size=256, required=False),
        'project_ids': fields.one2many('npo.project', 'project_categ_id', 'Projects under this Category', readonly=False),
        'active': fields.boolean('Active'), 
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The name of this project category must be unique !"),
    ]
    
npo_project_categ()


class npo_project(osv.osv):
    _name = 'npo.project'
    _description = 'Project'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'description': fields.char('Description', size=256, required=False),
        'project_categ_id': fields.many2one('npo.project.categ', 'Project Category'),
        'project_line_ids': fields.one2many('npo.project.line', 'project_id', 'Project Lines under this project', readonly=False),
        'active': fields.boolean('Active'), 
    }
    _defaults = {
        'active': True,
        'project_categ_id': lambda self, cr, uid, c: c.get('active_id', False),
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "The name of this project must be unique !"),
    ]
    
npo_project()

class npo_project_line(osv.osv):
    _name = 'npo.project.line'
    _description = 'Project Line'
    
    def _get_sum_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for project_line in self.browse(cr, uid, ids, context=context):
            res[project_line.id] = {
                'budget_alloc_total': 0.0,
                'budget_used_total': 0.0,
                'budget_diff_total': 0.0,
            }
            for budget_line in project_line.budget_line:
                res[project_line.id]['budget_alloc_total'] += budget_line.budget_alloc
                res[project_line.id]['budget_used_total'] += budget_line.budget_used
            res[project_line.id]['budget_diff_total'] = res[project_line.id]['budget_alloc_total'] - res[project_line.id]['budget_used_total']
            
        return res
    
    def _get_project_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('npo.project.line.budget.line').browse(cr, uid, ids, context=context):
            result[line.project_line_id.id] = True
        return result.keys()
    
    def _get_project_line2(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.bank.statement.line').browse(cr, uid, ids, context=context):
            result[line.project_line_id.id] = True
        return result.keys()
    
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'description': fields.char('Description', size=256, required=False),
        'project_id': fields.many2one('npo.project', 'Project'),
        'project_categ_id': fields.related('project_id', 'project_categ_id', type='many2one', relation='npo.project.categ', string='Project Category', store=True, readonly=True),
        'budget_alloc_total': fields.function(_get_sum_total, type='float', string='Total Budget Allocation',
            store={
                'npo.project.line': (lambda self, cr, uid, ids, c={}: ids, ['budget_line'], 10),
                'npo.project.line.budget.line': (_get_project_line, ['budget_alloc', 'budget_used', 'budget_diff'], 10),
                'account.bank.statement.line': (_get_project_line2, ['amount', 'project_line_id', 'obi_id'], 20),
            },
             multi='sums'
        ),
        'budget_used_total': fields.function(_get_sum_total, type='float', string='Total Budget Used',
            store={
                'npo.project.line': (lambda self, cr, uid, ids, c={}: ids, ['budget_line'], 10),
                'npo.project.line.budget.line': (_get_project_line, ['budget_alloc', 'budget_used', 'budget_diff'], 10),
                'account.bank.statement.line': (_get_project_line2, ['amount', 'project_line_id', 'obi_id'], 20),
            },
             multi='sums'
        ),
        'budget_diff_total': fields.function(_get_sum_total, type='float', string='Total Budget Difference',
             store={
                'npo.project.line': (lambda self, cr, uid, ids, c={}: ids, ['budget_line'], 10),
                'npo.project.line.budget.line': (_get_project_line, ['budget_alloc', 'budget_used', 'budget_diff'], 10),
                'account.bank.statement.line': (_get_project_line2, ['amount', 'project_line_id', 'obi_id'], 20),
            },
             multi='sums'
        ),
        'budget_line': fields.one2many('npo.project.line.budget.line', 'project_line_id', 'Budget Lines', readonly=False),
        'account_id': fields.many2one('account.account','Account',
            required=True),
        'active': fields.boolean('Active'), 
    }
    _defaults = {
        'active': True,
        'project_id': lambda self, cr, uid, c: c.get('active_id', False),
        'budget_alloc_total': 0.0,
        'budget_used_total': 0.0,
        'budget_diff_total': 0.0
    }
    _sql_constraints = [
        ('uniq_name', 'unique(name, project_id)', "The name of this project line must be unique !"),
    ]
    
npo_project_line()


class npo_project_line_budget_line(osv.osv):
    _name = 'npo.project.line.budget.line'
    _description = 'Project Line Budget Line'

    def _get_budget_line(self, cr, uid, ids, context=None):
        budget_line_ids = []
        for line in self.pool.get('account.bank.statement.line').browse(cr, uid, ids, context=context):
            budget_line_ids += self.pool.get('npo.project.line.budget.line').search(cr, uid, [('project_line_id', '=', line.project_line_id.id), ('obi_id', '=', line.obi_id.id)])
        return budget_line_ids
    
    def _get_budget_used(self, cr, uid, ids, name, args, context):
        if not ids: return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'budget_used': 0.0,
                'budget_diff': 0.0,
            }
            cr.execute("select sum(amount) from account_bank_statement_line sl \
                            inner join account_bank_statement s on s.id = sl.statement_id \
                            where project_line_id = %s and obi_id = %s",
                         (line.project_line_id.id, line.obi_id.id))
            result = dict(cr.dictfetchone())
            res[line.id]['budget_used'] = result['sum'] and - result['sum'] or 0.0
            res[line.id]['budget_diff'] = line.budget_alloc - res[line.id]['budget_used']
        return res
    
    _columns = {
        'project_line_id': fields.many2one('npo.project.line', 'Project Line', ondelete="cascade"),
        'budget_alloc': fields.float('Budget Allocation'),
        'budget_used': fields.function(_get_budget_used, type='float', string='Budget Used',
                        store={
                            'account.bank.statement.line': (_get_budget_line, ['amount', 'project_line_id', 'obi_id'], 10),
                        },
                         multi="budget"
        ),
        'budget_diff': fields.function(_get_budget_used, type='float', string='Budget Difference',
                        store={
                            'account.bank.statement.line': (_get_budget_line, ['amount', 'project_line_id', 'obi_id'], 10),
                            'npo.project.line.budget.line': (lambda self, cr, uid, ids, c={}: ids, ['budget_alloc'], 10),
                        },
                         multi="budget"
        ),
        'obi_id': fields.many2one('npo.obi', 'Donor', required=True),
    }
    _defaults = {
        'budget_alloc': 0.0,
        'budget_used': 0.0,
        'budget_diff': 0.0
    }
    _sql_constraints = [
        ('uniq_donor', 'unique(obi_id, project_line_id)', "Donor must be unique !"),
    ]
    
npo_project_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
