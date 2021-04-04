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
            
        user = self.env['hr.leave'].search([('id', '=', active_id)], limit=1)
        comment =  self.env['create.leave.comment'].sudo().search([('id', '=', new.id)], limit=1).comment 
        all_emails = ""
        approved = ""
        notApproved = ""
        for user_obj in user.leave_approvals:
            clicked = 0
            # if user_obj.validation_status != True:
            if user_obj.validators_type == 'direct_manager' and user.employee_id.parent_id.id != False:
                if user_obj.validation_status == True:
                    if approved != "":
                        if str("Direct Manager") not in approved:
                            approved = approved + "," + str("Direct Manager")
                    else:
                        approved = str("Direct Manager")

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
                        if approved != "":
                            if str("Direct Manager") not in approved:
                                approved = approved + "," + str("Direct Manager")
                        else:
                            approved = str("Direct Manager")

                if  clicked != 1 and user_obj.validation_status != True:
                    if notApproved != "":
                        if str("Direct Manager") not in notApproved:
                            notApproved = notApproved + "," + str("Direct Manager")
                    else:
                        notApproved = str("Direct Manager")         
            if  user_obj.validators_type == 'position':
                employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id),('user_id','=',current_uid)])
                employee_email = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id)])
                if user_obj.validation_status == True:
                    if approved != "":
                        if str(user_obj.holiday_validators_position.name) not in approved:
                            approved = approved + "," + str(user_obj.holiday_validators_position.name)
                    else:
                        approved = str(user_obj.holiday_validators_position.name)
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
                    if approved != "":
                        if str(user_obj.holiday_validators_position.name) not in approved:
                            approved = approved + "," + str(user_obj.holiday_validators_position.name)
                    else:
                        approved = str(user_obj.holiday_validators_position.name)
                if  clicked != 1 and user_obj.validation_status != True:
                    if notApproved != "":
                        if str(user_obj.holiday_validators_position.name) not in notApproved:
                            notApproved = notApproved + "," + str(user_obj.holiday_validators_position.name)
                    else:
                        notApproved = str(user_obj.holiday_validators_position.name)            
            if  user_obj.validators_type == 'user':
                if user_obj.validation_status == True:
                    if approved != "":
                        if str(user_obj.holiday_validators_user.name) not in approved:
                            approved = approved + "," + str(user_obj.holiday_validators_user.name)
                    else:
                        approved = str(user_obj.holiday_validators_user.name)
                if all_emails != "":
                    if str(user_obj.holiday_validators_user.login) not in all_emails:
                        all_emails = all_emails + "," +str(user_obj.holiday_validators_user.login)
                else:
                    all_emails = str(user_obj.holiday_validators_user.login)
                if  clicked != 1 and user_obj.validation_status != True:
                    if notApproved != "":
                        if str(user_obj.holiday_validators_user.name) not in notApproved:
                            notApproved = notApproved + "," + str(user_obj.holiday_validators_user.name)
                    else:
                        notApproved = str(user_obj.holiday_validators_user.name)    
                if user_obj.holiday_validators_user.id == current_uid:
                    validation_obj = user.leave_approvals.search(
                                [('id', '=', user_obj.id)])
                    validation_obj.validation_status = True
                    validation_obj.validation_refused = False
                    validation_obj.leave_comments = comment
            if not(user_obj.approval != True or (user_obj.approval == True and user_obj.validation_status == True)): 
                break 
            user.all_emails = all_emails        
            user.approved_emails = approved
            user.notApproved = notApproved

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