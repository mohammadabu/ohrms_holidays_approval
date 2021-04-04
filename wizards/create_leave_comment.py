from odoo import models, api,exceptions, fields, _

class CreateLeaveComment(models.TransientModel):
    _name = 'create.leave.comment'
    comment = fields.Text()
    
    def create_comment(self):
        view_id=self.env['create.leave.comment']
        new = view_id.sudo().create({
            'comment' :self.comment
        })
        current_uid = self.env.uid
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        li = {}
        if self.env.context.get('active_id'):
            active_id = self.env.context.get('active_id')
        else:
            active_id = self.id
            
        user = self.env['hr.leave'].sudo().search([('id', '=', active_id)], limit=1)
        comment =  self.env['create.leave.comment'].sudo().search([('id', '=', new.id)], limit=1).comment 
        all_emails = ""
        approved = ""
        notApproved = ""
        holiday_status_id = ""
        employee_id = ""
        request_date_from = ""
        request_date_to = ""
        number_of_days = ""
        res_id = ""
        message = ""
        for user_obj in user.leave_approvals:
            clicked = 0
            # if user_obj.validation_status != True:
            if user_obj.validators_type == 'direct_manager' and user.employee_id.parent_id.id != False:
                if user_obj.validation_status == True:
                    str_pos = "The <b>Direct Manager</b> approved your time off request<br>" 
                    if approved != "":
                        if str(str_pos) not in approved:
                            approved = approved + "" + str(str_pos)
                    else:
                        approved = str(str_pos)

                if user.employee_id.parent_id.user_id.id != False:
                    if all_emails != "":
                        if str(user.employee_id.parent_id.user_id.login) not in all_emails:
                            all_emails = all_emails + "," + str(user.employee_id.parent_id.user_id.login)
                    else:
                        all_emails = str(user.employee_id.parent_id.user_id.login)
                    if user.employee_id.parent_id.user_id.id == current_uid:
                        validation_obj = user.leave_approvals.search(
                                [('id', '=', user_obj.id)])
                        validation_obj.validation_status = True
                        validation_obj.validation_refused = False
                        validation_obj.leave_comments = comment
                        clicked = 1
                        str_pos = "The <b>Direct Manager</b> approved your time off request<br>" 
                        if approved != "":
                            if str(str_pos) not in approved:
                                approved = approved + "" + str(str_pos)
                        else:
                            approved = str(str_pos)

                if  clicked != 1 and user_obj.validation_status != True:
                    str_pos = "- Direct Manager<br>"
                    if notApproved != "":
                        if str(str_pos) not in notApproved:
                            notApproved = notApproved + "" + str(str_pos)
                    else:
                        notApproved = str(str_pos)         
            if  user_obj.validators_type == 'position':
                employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id),('user_id','=',current_uid)])
                employee_email = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id)])
                if user_obj.validation_status == True:
                    str_pos = "The position <b>"+user_obj.holiday_validators_position.name+"</b> approved your time off request<br>"
                    if approved != "": 
                        if str(str_pos) not in approved:
                            approved = approved + "" + str(str_pos)
                    else:
                        approved = str(str_pos)
                for emp in employee_email:
                    if all_emails != False:
                        if str(emp.user_id.login) not in all_emails:
                            all_emails = all_emails + "," +str(emp.user_id.login)
                    else:
                        all_emails = str(emp.user_id.login)
                if len(employee) > 0:
                    validation_obj = user.leave_approvals.search(
                                [('id', '=', user_obj.id)])
                    validation_obj.validation_status = True
                    validation_obj.validation_refused = False
                    validation_obj.leave_comments = comment
                    clicked = 1
                    str_pos = "The position <b>"+user_obj.holiday_validators_position.name+"</b> approved your time off request<br>"
                    if approved != "":
                        if str(str_pos) not in approved:
                            approved = approved + "" + str(str_pos)
                    else:
                        approved = str(str_pos)
                if  clicked != 1 and user_obj.validation_status != True:
                    str_pos = "- "+user_obj.holiday_validators_position.name+"<br>"
                    if notApproved != "":
                        if str(str_pos) not in notApproved:
                            notApproved = notApproved + "" + str(str_pos)
                    else:
                        notApproved = str(str_pos)            
            if  user_obj.validators_type == 'user':
                if user_obj.validation_status == True:
                    str_pos = "<b>"+user_obj.holiday_validators_user.name+"</b> approved to your time off request<br>"
                    if approved != "":
                        if str(str_pos) not in approved:
                            approved = approved + "" + str(str_pos)
                    else:
                        approved = str(str_pos)
                if all_emails != "":
                    if str(user_obj.holiday_validators_user.login) not in all_emails:
                        all_emails = all_emails + "," +str(user_obj.holiday_validators_user.login)
                else:
                    all_emails = str(user_obj.holiday_validators_user.login)
                if user_obj.holiday_validators_user.id == current_uid:
                    validation_obj = user.leave_approvals.search(
                                [('id', '=', user_obj.id)])
                    validation_obj.validation_status = True
                    validation_obj.validation_refused = False
                    validation_obj.leave_comments = comment
                    clicked = 1
                if  clicked != 1 and user_obj.validation_status != True:
                    str_pos = "- "+user_obj.holiday_validators_user.name+"<br>"
                    if notApproved != "":
                        if str(str_pos) not in notApproved:
                            notApproved = notApproved + "" + str(str_pos)
                    else:
                        notApproved = str(str_pos)        
            # if not(user_obj.approval != True or (user_obj.approval == True and user_obj.validation_status == True)): 
            #     break 
            user.all_emails = all_emails        
            user.approved_emails = approved
            user.notApproved_emails = notApproved

            holiday_status_id = user.holiday_status_id.id
            employee_id = user.employee_id.id
            request_date_from = user.request_date_from
            request_date_to = user.request_date_to
            number_of_days = user.number_of_days  
            res_id = user.id
        employee = self.env['hr.employee'].sudo().search([('id','=',employee_id)])
        if not notApproved != "":
            message += ('<h2>Dear %s<h2><br/>') % (employee.name)
        if notApproved != "":
            message += ('<h4>Request approval to leave by %s<h4><br/>') % (employee.name)
        else:
            message += '<h4>The Request was officially accepted <h4><br/>'  
        message += ('<p style="font-size: 12px;">From %s</p><br/>') % (request_date_from)
        message += ('<p style="font-size: 12px;">To %s</p><br/>') % (request_date_to)
        message += ('<p style="font-size: 12px;">Duration: %s</p><br/>') % (number_of_days)
        if notApproved != "":
            message += ('%s') % (approved)
            message += '<br><h4>Waiting for approval of the request : </h4>'
            message += ('%s') % (notApproved)      
        body_html = self.create_body_for_email(message,res_id)
        email_html = self.create_header_footer_for_email(holiday_status_id,employee_id,body_html)     
        subject = "Approval of the time off request"      
        if notApproved == "":
            subject = "The request for leave has been accepted"
        value = {
            'subject': 'Approval of the time off request',
            'body_html': email_html,
            'email_to': all_emails,
            'email_cc': '',
            'auto_delete': False,
            'email_from': 'axs-sa.com',
        }
        mail_id = self.env['mail.mail'].sudo().create(value)
        mail_id.sudo().send()


        approval_flag = True
        for user_obj in user.leave_approvals:
            if not user_obj.validation_status:
                approval_flag = False
        if approval_flag:
            user.filtered(
                lambda hol: hol.validation_type == 'both').sudo().write(
                {'state': 'validate1',
                 'first_approver_id': current_employee.id})
            user.filtered(lambda
                              hol: not hol.validation_type == 'both').sudo().action_validate()
            if not user.env.context.get('leave_fast_create'):
                user.activity_update()
            return True
        else:
            return False

    def cancel_comment(self):
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