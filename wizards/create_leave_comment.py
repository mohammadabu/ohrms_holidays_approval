from odoo import models, api, fields, _

class CreateLeaveComment(models.TransientModel):
    _name = 'create.leave.comment'
    comment = fields.Text()
    