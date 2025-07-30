# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    location_id = fields.Many2one(
        string="Location",
        comodel_name="stock.location",
        ondelete="restrict",
    )
    current_warehouse_id = fields.Many2one(
        string="Current Warehouse",
        comodel_name="stock.warehouse",
        compute="_compute_current_warehouse_id",
        store=True,
        compute_sudo=True,
    )

    @api.depends(
        "address_id",
    )
    def _compute_current_warehouse_id(self):
        for record in self:
            result = False
            Warehouse = self.env["stock.warehouse"]
            if record.address_id:
                if record.address_id.parent_id:
                    parent = record.address_id.parent_id
                    criteria = [("partner_id", "=", parent.id)]
                    warehouses = Warehouse.search(criteria)
                    if len(warehouses) > 0:
                        result = warehouses[0]
            record.current_warehouse_id = result

    def action_create_employee_location(self):
        for record in self.sudo():
            record._create_employee_location()

    def action_delete_employee_location(self):
        for record in self.sudo():
            record._delete_employee_location()

    def _create_employee_location(self):
        self.ensure_one()
        employee_location_type = self.env.ref(
            "ssi_hr_employee_stock.location_type_employee"
        )
        data = {
            "name": self.name,
            "usage": "internal",
            "type_id": employee_location_type.id,
        }
        location = self.env["stock.location"].create(data)
        self.write(
            {
                "location_id": location.id,
            }
        )

    def _delete_employee_location(self):
        self.ensure_one()
        location = self.location_id
        if not location:
            return True

        self.write(
            {
                "location_id": False,
            }
        )
        location.unlink()
