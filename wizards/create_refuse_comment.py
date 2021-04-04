from odoo import models, api, fields, _

class CreateLeaveComment(models.TransientModel):
    _name = 'create.refuse.comment'
    comment = fields.Text()
    


    def create_refuse_comment(self):
        view_id=self.env['create.refuse.comment']
        new = view_id.sudo().create({
            'comment' :self.comment
        })
        current_employee = self.env['hr.employee'].sudo().search(
                [('user_id', '=', self.env.uid)], limit=1)
        approval_access = False
        current_uid = self.env.uid
        if self.env.context.get('active_id'):
            active_id = self.env.context.get('active_id')
        else:
            active_id = self.id
        
        leave_self = self.env['hr.leave'].sudo().search([('id', '=', active_id)], limit=1)
        comment =  self.env['create.refuse.comment'].sudo().search([('id', '=', new.id)], limit=1).comment
        message = ""
        
        for l2 in leave_self.leave_approvals: 
            # direct manager
            if l2.validators_type == 'direct_manager' and leave_self.employee_id.parent_id.id != False:
                if leave_self.employee_id.parent_id.user_id.id != False:
                    if leave_self.employee_id.parent_id.user_id.id == current_uid:
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
            # if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
            #     break     
        holiday_status_id = user.holiday_status_id.id
        employee_id = user.employee_id.id
        request_date_from = user.request_date_from
        request_date_to = user.request_date_to
        number_of_days = user.number_of_days  
        all_emails = user.all_emails
        res_id = user.id
        employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
        message += ('<h2>Dear %s<h2><br/>') % (employee.name)
        message += ('<h4>The leave request was refused by  %s<h4><br/>') % (employee.name)
        message += ('<p style="font-size: 12px;">From %s</p><br/>') % (request_date_from)
        message += ('<p style="font-size: 12px;">To %s</p><br/>') % (request_date_to)
        message += ('<p style="font-size: 12px;">Duration: %s</p><br/>') % (number_of_days)    
        body_html = self.create_body_for_email(message,res_id)
        email_html = self.create_header_footer_for_email(holiday_status_id,employee_id,body_html)     
        subject = "Refused leave"      
        value = {
            'subject': 'Approval of the time off request',
            'body_html': email_html,
            'email_to': all_emails,
            'email_cc': '',
            'auto_delete': False,
            'email_from': 'axs-sa.com',
        }
        if approval_access:
            for holiday in leave_self:
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
            leave_self._remove_resource_leave()
            leave_self.activity_update()
            for user_obj in leave_self.leave_approvals:    
                if user_obj.validators_type == 'direct_manager' and leave_self.employee_id.parent_id.id != False:
                    if leave_self.employee_id.parent_id.user_id.id != False:
                        if leave_self.employee_id.parent_id.user_id.id == current_uid:

                            validation_obj = leave_self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                            
                            validation_obj.validation_status = False
                            validation_obj.validation_refused = True
                            validation_obj.leave_comments = comment
                if  user_obj.validators_type == 'position':
                    employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id),('user_id','=',current_uid)])
                    if len(employee) > 0:

                        validation_obj = leave_self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])

                        validation_obj.validation_status = False
                        validation_obj.validation_refused = True
                        validation_obj.leave_comments = comment
                if  user_obj.validators_type == 'user':
                    if user_obj.holiday_validators_user.id == current_uid:

                        validation_obj = leave_self.leave_approvals.search(
                                    [('id', '=', user_obj.id)])

                        validation_obj.validation_status = False
                        validation_obj.validation_refused = True
                        validation_obj.leave_comments = comment








            mail_id = self.env['mail.mail'].sudo().create(value)
            mail_id.sudo().send()
            return True
        else:
            for holiday in leave_self:
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
            leave_self._remove_resource_leave()
            leave_self.activity_update()
            mail_id = self.env['mail.mail'].sudo().create(value)
            mail_id.sudo().send()
            return True
    def cancel_refuse_comment(self):
        return {'type': 'ir.actions.act_window_close'}        