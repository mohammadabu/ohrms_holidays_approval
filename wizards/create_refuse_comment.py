from odoo import models, api, fields, _

class CreateLeaveComment(models.TransientModel):
    _name = 'create.refuse.comment'
    comment = fields.Text()
    


    def create_refuse_comment(self):
        view_id=self.env['create.refuse.comment']
        new = view_id.sudo().create({
            'comment' :self.comment
        })
        current_employee = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1)
        approval_access = False
        current_uid = self.env.uid
        self.is_refused_user_id = False
        comment =  self.env['create.refuse.comment'].sudo().search([('id', '=', new.id)], limit=1).comment
        for l2 in self.leave_approvals: 
            # direct manager
            if l2.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                if self.employee_id.parent_id.user_id.id != False:
                    if self.employee_id.parent_id.user_id.id == current_uid:
                        approval_access= True
            # position
            if  l2.validators_type == 'position':
                employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
                if len(employees) > 0:
                    for employee in employees:
                        if employee.user_id.id == current_uid:
                            approval_access= True
            #user
            if  l2.validators_type == 'user':
                if l2.holiday_validators_user.id == current_uid:
                    approval_access= True
            if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                break     
        if approval_access:
            for holiday in self:
                if holiday.state not in ['confirm', 'validate', 'validate1']:
                    raise UserError(_(
                        'Leave request must be confirmed or validated in order to refuse it.'))
                if holiday.state == 'validate1':
                    holiday.sudo().write({'state': 'refuse',
                                        'first_approver_id': current_employee.id})
                else:
                    holiday.sudo().write({'state': 'refuse',
                                        'second_approver_id': current_employee.id})
                # Delete the meeting
                if holiday.meeting_id:
                    holiday.meeting_id.unlink()
                # If a category that created several holidays, cancel all related
                holiday.linked_request_ids.action_refuse()
            self._remove_resource_leave()
            self.activity_update()
            for user_obj in self.leave_approvals:
                if user_obj.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                    if self.employee_id.parent_id.user_id.id != False:
                        if self.employee_id.parent_id.user_id.id == current_uid:
                            validation_obj = self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                            validation_obj.validation_status = False
                            validation_obj.validation_refused = True
                            validation_obj.leave_comments = comment
                if  user_obj.validators_type == 'position':
                    employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id),('user_id','=',current_uid)])
                    if len(employee) > 0:
                        validation_obj = self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                        validation_obj.validation_status = False
                        validation_obj.validation_refused = True
                        validation_obj.leave_comments = comment
                if  user_obj.validators_type == 'user':
                    if user_obj.holiday_validators_user.id == current_uid:
                        validation_obj = self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                        validation_obj.validation_status = False
                        validation_obj.validation_refused = True
                        validation_obj.leave_comments = comment
            return True
        else:
            for holiday in self:
                if holiday.state not in ['confirm', 'validate', 'validate1']:
                    raise UserError(_(
                        'Leave request must be confirmed or validated in order to refuse it.'))

                if holiday.state == 'validate1':
                    holiday.write({'state': 'refuse',
                                'first_approver_id': current_employee.id})
                else:
                    holiday.write({'state': 'refuse',
                                'second_approver_id': current_employee.id})
                # Delete the meeting
                if holiday.meeting_id:
                    holiday.meeting_id.unlink()
                # If a category that created several holidays, cancel all related
                holiday.linked_request_ids.action_refuse()
            self._remove_resource_leave()
            self.activity_update()
            return True
    def cancel_refuse_comment(self):
        return {'type': 'ir.actions.act_window_close'}        