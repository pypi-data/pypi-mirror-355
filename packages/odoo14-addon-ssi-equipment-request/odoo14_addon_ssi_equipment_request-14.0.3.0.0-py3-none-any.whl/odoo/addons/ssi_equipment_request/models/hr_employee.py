# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    equipment_request_route_ids = fields.Many2many(
        string="Equipment Request Routes",
        comodel_name="stock.location.route",
        column1="employee_id",
        column2="route_id",
        relation="rel_employee_2_equipment_request_route",
    )

    def action_create_equipment_request_route(self):
        for record in self.sudo():
            record._create_equipment_request_route()

    def _create_equipment_request_route(self):
        self.ensure_one()
        criteria = [
            ("company_id", "=", self.env.company.id),
        ]
        route_ids = []
        Warehouse = self.env["stock.warehouse"]
        for warehouse in Warehouse.search(criteria):
            route = warehouse._create_equipment_request_route(self)
            route_ids.append(route.id)
        self.write(
            {
                "equipment_request_route_ids": [(6, 0, route_ids)],
            }
        )
