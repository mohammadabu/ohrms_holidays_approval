import re
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import email_split
from pytz import timezone, UTC

class HrLeaveTypes(models.Model):
    """ Extend model to add multilevel approval """
    _inherit = 'hr.leave.type'

    multi_level_validation = fields.Boolean(string='Multiple Level Approval',
                                            help="If checked then multi-level approval is necessary")
    validation_type = fields.Selection(selection_add=[('multi', 'Direct Manager and HR')])
    leave_validators = fields.One2many('hr.holidays.validators',
                                       'hr_holiday_status',
                                       string='Leave Validators', help="Leave validators")

    @api.onchange('validation_type')
    def enable_multi_level_validation(self):
        """ Enabling the boolean field of multilevel validation"""
        if self.validation_type == 'multi':
            self.multi_level_validation = True
        else:
            self.multi_level_validation = False

    @api.onchange('multi_level_validation')
    def disable_double_validation(self):
        """ Disable doy=uble validation when multi level a
        pproval is disabled """
        if self.multi_level_validation:
            self.double_validation = False

    @api.onchange('double_validation')
    def disable_multi_approval(self):
        """ Disable multi level approval when double validation is enabled """
        if self.double_validation:
            self.multi_level_validation = False

    def write(self,values):
        rtn = super(HrLeaveTypes,self).write(values)
        if self.validation_type == "multi":
            if len(self.leave_validators) < 1:
                raise UserError(_("At Least Add One leave_validators"))
        return rtn                                   

    
class HrLeaveValidators(models.Model):
    """ Model for leave validators in Leave Types configuration """
    _name = 'hr.holidays.validators'

    hr_holiday_status = fields.Many2one('hr.leave.type')
    validators_type = fields.Selection(
        [
            ('direct_manager','Direct Manager'),
            ('position','Position'),
            ('user','User')
        ]
    )
    holiday_validators_user = fields.Many2one('res.users',
                                         string='Leave Validators', help="Leave validators",
                                         domain="[('share','=',False)]")
    holiday_validators_position = fields.Many2one('hr.job')                                     
    approval = fields.Boolean()                                   


class LeaveValidationStatus(models.Model):
    """ Model for leave validators and their status for each leave request """
    _name = 'leave.validation.status'

    holiday_status = fields.Many2one('hr.leave')

    validators_type = fields.Selection(
        [
            ('direct_manager','Direct Manager'),
            ('position','Position'),
            ('user','User')
        ]
    )
    holiday_validators_user = fields.Many2one('res.users',
                                         string='Leave Validators', help="Leave validators",
                                         domain="[('share','=',False)]")
    holiday_validators_position = fields.Many2one('hr.job')                                     
    approval = fields.Boolean()   
    validation_status = fields.Boolean(string='Approved', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Approved")
    validation_refused = fields.Boolean(string='Refused', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Refused")                                   
    leave_comments = fields.Text(string='Comments', help="Comments",readonly=True)

    @api.onchange('validators_type','holiday_validators_user','holiday_validators_position','approval')
    def prevent_change(self):
        """ Prevent Changing leave validators from leave request form """
        raise UserError(_(
            "Changing leave validators is not permitted. You can only change "
            "it from Leave Types Configuration"))
class HrLeave(models.Model):
    _inherit = 'hr.leave'

    leave_approvals = fields.One2many('leave.validation.status',
                                      'holiday_status',
                                      string='Leave Validators',
                                      track_visibility='always', help="Leave approvals")

    multi_level_validation = fields.Boolean(string='Multiple Level Approval',
                                            related='holiday_status_id.multi_level_validation',
                                            help="If checked then multi-level approval is necessary") 
    
    is_approved_user_id = fields.Boolean(default=False, compute='_check_is_approved_user_id')  
      
    def _check_is_approved_user_id(self):
        current_uid = self.env.uid
        self.is_approved_user_id= False
        for l2 in self.leave_approvals: 
            #for approval button
            if l2.validation_status != True:
                # direct manager
                if l2.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                    if self.employee_id.parent_id.user_id.id != False:
                        if self.employee_id.parent_id.user_id.id == current_uid:
                            self.is_approved_user_id= True
                            break
                # position
                if  l2.validators_type == 'position':
                    employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
                    if len(employees) > 0:
                        for employee in employees:
                            if employee.user_id.id == current_uid:
                                self.is_approved_user_id= True
                        break
                #user
                if  l2.validators_type == 'user':
                    if l2.holiday_validators_user.id == current_uid:
                        self.is_approved_user_id= True
                        break
                if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                    break        
    is_refused_user_id = fields.Boolean(default=False, compute='_check_is_refused_user_id')
    def _check_is_refused_user_id(self):
        current_uid = self.env.uid
        self.is_refused_user_id = False
        for l2 in self.leave_approvals: 
            # direct manager
            if l2.validators_type == 'direct_manager' and self.employee_id.parent_id.id != False:
                if self.employee_id.parent_id.user_id.id != False:
                    if self.employee_id.parent_id.user_id.id == current_uid:
                        self.is_refused_user_id= True
                        # break
            # position
            if  l2.validators_type == 'position':
                employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
                if len(employees) > 0:
                    for employee in employees:
                        if employee.user_id.id == current_uid:
                            self.is_refused_user_id= True
                    # break
            #user
            if  l2.validators_type == 'user':
                if l2.holiday_validators_user.id == current_uid:
                    self.is_refused_user_id= True
                    # break
            if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                break        
    @api.onchange('holiday_status_id')
    def add_validators(self):
        """ Update the tree view and add new validators
        when leave type is changed in leave request form """
        if self.validation_type == "multi":
            li = []
            self.leave_approvals = [(5, 0, 0)]
            for l in self.holiday_status_id.leave_validators:
                li.append((0, 0, {
                    'validators_type': l.validators_type,
                    'holiday_validators_user': l.holiday_validators_user.id,
                    'holiday_validators_position': l.holiday_validators_position.id,
                    'approval': l.approval,
                }))
            self.leave_approvals = li
    def _get_approval_requests(self):
        """ Action for Approvals menu item to show approval
        requests assigned to current user """
        current_uid = self.env.uid
        hr_holidays = self.env['hr.leave'].sudo().search([('state','=','confirm'),('holiday_status_id.validation_type','=','multi')])
        li = []
        for l in hr_holidays:
            for l2 in l.leave_approvals: 
                # direct manager
                if l2.validators_type == 'direct_manager' and l.employee_id.parent_id.id != False:
                    if l.employee_id.parent_id.user_id.id != False:
                        if l.employee_id.parent_id.user_id.id == current_uid:
                            li.append(l.id)
                # position
                if  l2.validators_type == 'position':
                    employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id),('user_id','=',current_uid)])
                    if len(employee) > 0:
                        li.append(l.id)
                #user
                if  l2.validators_type == 'user':
                    if l2.holiday_validators_user.id == current_uid:
                        li.append(l.id)
                if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                    break                                 
        value = {
            'domain': str([('id', 'in', li)]),
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Approvals'),
            'res_id': self.id,
            'target': 'current',
            'create': False,
            'edit': False,
        }
        return value
    def action_approve(self):
        
        """ Chack if any pending tasks is added if so reassign the pending
        task else call approval """
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if self.multi_level_validation:
            if any(holiday.state != 'confirm' for holiday in self):
                raise UserError(_(
                    'Leave request must be confirmed ("To Approve") in order to approve it.'))
            ohrmspro_vacation_project = self.sudo().env['ir.module.module'].search(
                [('name', '=', 'ohrmspro_vacation_project')],
                limit=1).state
            if ohrmspro_vacation_project == 'installed':
                return self.env['hr.leave'].check_pending_task(self)
            else:
                return self.approval_check()
        else:
            rtn = super(HrLeave,self).action_approve()
            return rtn          
    def approval_check(self):
        """ Check all leave validators approved the leave request if approved
         change the current request stage to Approved"""   
        return {
                'type': 'ir.actions.act_window',
                'name': 'Reason for Approval',
                'res_model': 'create.leave.comment',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('ohrms_holidays_approval.view_create_leave_comment',False).id,
                'target': 'new',
        }
    def action_refuse(self):
        """ Refuse the leave request if the current user is in
        validators list """
        if self.multi_level_validation: 
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Reason for Refused',
                    'res_model': 'create.refuse.comment',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'view_id': self.env.ref('ohrms_holidays_approval.view_create_refuse_comment',False).id,
                    'target': 'new',
            }
        else:
            rtn = super(HrLeave,self).action_refuse()
            return rtn        
    def action_draft(self):
        """ Reset all validation status to false when leave request
        set to draft stage"""
        if self.multi_level_validation:
            for user in self.leave_approvals:
                user.validation_status = False
                user.validation_refused = False
        return super(HrLeave, self).action_draft()
    @api.model_create_multi
    def create(self,vals):
        for values in vals:
            holiday_status_id = values.get('holiday_status_id')
            employee_id = values.get('employee_id')
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        if hr_holidays.validation_type == "multi":
            
            body_html = self.create_header_for_email(holiday_status_id,employee_id)
            value = {
                'subject': 'Foo',
                'body_html': body_html,
                'email_to': 'foo@example.com,bar@example.com',
                'email_cc': 'qux@example.com',
                'auto_delete': False,
                'email_from': 'foobar@example.com',
            }
            mail_id = self.env['mail.mail'].sudo().create(value)
            mail_id.sudo().send()
      
        rtn = super(HrLeave,self).create(vals)
        return rtn          


    def create_header_for_email(self,holiday_status_id,employee_id):
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        leave_type = hr_holidays.name
        company_id = employee_id.company_id
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
        header +=                                  ('<img src="/logo.png?company=%s" style="padding: 0px; margin: 0px; height: auto; width: 80px;" alt=""/>') % (company_id)
        header +=                               '</td></tr>'
        header +=                               '<tr><td colspan="2" style="text-align:center;">'
        header +=                                   '<hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>'
        header +=                               '</td></tr>'
        header +=                           '</table>'
        header +=                       '</td>'
        header +=                   '</tr>'
        header +=               '</tbody>'
        header +=           '</table>'
        header +=       '</td>'
        header +=     '</tr>'
        header +=   '</table>'
        return header



