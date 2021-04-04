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
        current_user_name = self.env['res.users'].sudo().search([('id', '=', current_uid)]).name
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
        holiday_status_id = leave_self.holiday_status_id.id
        employee_id = leave_self.employee_id.id
        request_date_from = leave_self.request_date_from
        request_date_to = leave_self.request_date_to
        number_of_days = leave_self.number_of_days  
        all_emails = leave_self.all_emails
        res_id = leave_self.id
        employee_login = self.env['hr.employee'].sudo().search([('id','=',employee_id)]).user_id.login
        employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
        message += ('<h2>Dear %s<h2><br/>') % (employee.name)
        message += ('<h4>The leave request was refused by  %s<h4><br/>') % (current_user_name)
        message += ('<p style="font-size: 12px;">From %s</p><br/>') % (request_date_from)
        message += ('<p style="font-size: 12px;">To %s</p><br/>') % (request_date_to)
        message += ('<p style="font-size: 12px;">Duration: %s</p><br/>') % (number_of_days)    
        body_html = self.create_body_for_email(message,res_id)
        email_html = self.create_header_footer_for_email(holiday_status_id,employee_id,body_html)       
        value = {
            'subject': 'Refused leave',
            'body_html': email_html,
            'email_to': all_emails + "," + employee_login,
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

    def create_body_for_email(self,message,res_id):
        body_html = ''
        body_html +='<tr>'
        body_html +=    '<td align="center" style="min-width: 590px;">'
        body_html +=        '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
        body_html +=            '<tr>'
        body_html +=                '<td valign="top" style="font-size: 13px;">'
        body_html +=                    '<p style="margin: 0px;font-size: 14px;">'
        body_html +=                        message
        body_html +=                    '</p>'
        body_html +=                    '<p style="margin-top: 24px; margin-bottom: 16px;">'
        body_html +=                        ('<a href="/mail/view?model=hr.leave&amp;res_id=%s" style="background-color:#875A7B; padding: 10px; text-decoration: none; color: #fff; border-radius: 5px;">') % (res_id)
        body_html +=                            'View Leave'
        body_html +=                        '</a>'
        body_html +=                    '</p>'
        body_html +=                    'Thanks,<br/>'
        body_html +=                '</td>'
        body_html +=            '</tr>'
        body_html +=            '<tr>'
        body_html +=                '<td style="text-align:center;">'
        body_html +=                    '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
        body_html +=                '</td>'
        body_html +=            '</tr>'
        body_html +=        '</table>'
        body_html +=    '</td>'
        body_html +='</tr>'
        return body_html

    def create_header_footer_for_email(self,holiday_status_id,employee_id,body_html):
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
        leave_type = hr_holidays.name
        company_id = employee.company_id.id
        header = ''
        header += '<table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;">'                      
        header +=   '<tr>'
        header +=       '<td align="center">' 
        header +=           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">'
        header +=               '<tbody>'

        header +=                   '<tr>'
        header +=                       '<td align="center" style="min-width: 590px;">'
        header +=                           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">'
        header +=                               '<tr><td valign="middle">'
        header +=                                   '<span style="font-size: 10px;">Leave Approval</span><br/>'
        header +=                                   '<span style="font-size: 20px; font-weight: bold;">'
        header +=                                       leave_type
        header +=                                   '</span>'
        header +=                               '</td><td valign="middle" align="right">'
        header +=                                  ('<img src="/logo.png?company=%s" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt=""/>') % (str(company_id))
        header +=                               '</td></tr>'
        header +=                               '<tr><td colspan="2" style="text-align:center;">'
        header +=                                   '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
        header +=                               '</td></tr>'
        header +=                           '</table>'
        header +=                       '</td>'
        header +=                   '</tr>'
        header +=                   body_html
        header +=                   '<tr>' 
        header +=                       '<td align="center" style="min-width: 590px;">' 
        header +=                           '<table border="0" cellpadding="0" cellspacing="0" width="622px" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 24px; border-collapse:separate;">'
        header +=                               '<tr><td valign="middle" align="left">'
        header +=                                   str(employee.company_id.name)
        header +=                               '</td></tr>'
        header +=                               '<tr><td valign="middle" align="left" style="opacity: 0.7;">'
        header +=                                   str(employee.company_id.phone)                
        if employee.company_id.email:
            header += ('<a href="mailto:%s" style="text-decoration:none; color: #454748;">%s</a>') % (str(employee.company_id.email),str(employee.company_id.email))
        if employee.company_id.website:
            header += ('<a href="%s" style="text-decoration:none; color: #454748;">') % (str(employee.company_id.website))    
        header +=                               '</td></tr>'
        header +=                           '</table>'
        header +=                       '</td>'
        header +=                   '</tr>'

        header +=               '</tbody>'
        header +=           '</table>'
        header +=       '</td>'
        header +=     '</tr>'
        header +=     '<tr>'
        header +=       '<td align="center" style="min-width: 590px;">'
        header +=           '<table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: #F1F1F1; color: #454748; padding: 8px; border-collapse:separate;">'
        header +=               '<tr><td style="text-align: center; font-size: 13px;">'
        header +=                   "Powered by "+ ('<a target="_blank" href="%s" style="color: #875A7B;">%s</a>') % (str(employee.company_id.website),str(employee.company_id.name)) 
        header +=               '</td></tr>'
        header +=           '</table>'
        header +=       '</td>'
        header +=     '</tr>'
        header +=   '</table>'
        return header        