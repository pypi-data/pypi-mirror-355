# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import SQL


class BudgetMonitorReport(models.Model):
    _inherit = "budget.monitor.report"

    revision_number = fields.Char()

    # Budget
    def _select_budget(self):
        select_budget_query = super()._select_budget()
        select_budget_query[70] = "b.revision_number::char as revision_number"
        return select_budget_query

    @api.model
    def _from_budget(self) -> SQL:
        return SQL("%s, b.revision_number", super()._from_budget())

    # All consumed
    def _select_statement(self, amount_type):
        select_statement = super()._select_statement(amount_type)
        select_statement[70] = "null::char as revision_number"
        return select_statement
