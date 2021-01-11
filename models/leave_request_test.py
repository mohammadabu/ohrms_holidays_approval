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
    validation_status = fields.Boolean(string='Approve Status', readonly=True,
                                       default=False,
                                       track_visibility='always', help="Status")
    leave_comments = fields.Text(string='Comments', help="Comments")

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
    test = fields.Text()                                       
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
        self.check_actions()
        for l in hr_holidays:
            for l2 in l.leave_approvals: 
                # direct manager
                if l2.validators_type == 'direct_manager' and l.employee_id.parent_id.id != False:
                    if l.employee_id.parent_id.user_id.id != False:
                        if l.employee_id.parent_id.user_id.id == current_uid:
                            li.append(l.id)
                            # self.check_actions(l)
                # position
                if  l2.validators_type == 'position':
                    employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id),('user_id','=',current_uid)])
                    if len(employee) > 0:
                        li.append(l.id)
                        # self.check_actions(l)
                #user
                if  l2.validators_type == 'user':
                    if l2.holiday_validators_user.id == current_uid:
                        li.append(l.id)
                        # self.check_actions(l)
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
        current_uid = self.env.uid
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        li = {}
        if self.env.context.get('active_id'):
            active_id = self.env.context.get('active_id')
        else:
            active_id = self.id
            
        user = self.env['hr.leave'].search([('id', '=', active_id)], limit=1)
        for user_obj in user.leave_approvals:
            if user_obj.validation_status != True:
                if user_obj.validators_type == 'direct_manager' and user.employee_id.parent_id.id != False:
                    if user.employee_id.parent_id.user_id.id != False:
                        if user.employee_id.parent_id.user_id.id == current_uid:
                            validation_obj = user.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                            validation_obj.validation_status = True
                if  user_obj.validators_type == 'position':
                    employee = self.env['hr.employee'].sudo().search([('multi_job_id','in',user_obj.holiday_validators_position.id),('user_id','=',current_uid)])
                    if len(employee) > 0:
                        validation_obj = user.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                        validation_obj.validation_status = True
                if  user_obj.validators_type == 'user':
                    if user_obj.holiday_validators_user.id == current_uid:
                        validation_obj = user.leave_approvals.search(
                                    [('id', '=', user_obj.id)])
                        validation_obj.validation_status = True
                if not(user_obj.approval != True or (user_obj.approval == True and user_obj.validation_status == True)): 
                    break 
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
    @api.model_create_multi
    def create(self,vals):
        for values in vals:
            holiday_status_id = values.get('holiday_status_id')
        hr_holidays = self.env['hr.leave.type'].sudo().search([('id','=',holiday_status_id)])
        if hr_holidays.validation_type == "multi":
            template_id = self.env.ref('ohrms_holidays_approval.custom_update_leave_approval_tempalte').id
            self.env['mail.template'].sudo().browse(template_id).send_mail(self.id,force_send=True)       
        rtn = super(HrLeave,self).create(vals)
        return rtn      

    def check_actions(self):
        current_uid = self.env.uid
        hr_holidays = self.env['hr.leave'].sudo().search([('state','=','confirm'),('holiday_status_id.validation_type','=','multi')])
        li = []
        for l in hr_holidays:
            l.test = False
            for l2 in l.leave_approvals: 
                # direct manager
                if l2.validators_type == 'direct_manager' and l.employee_id.parent_id.id != False:
                    if l.employee_id.parent_id.user_id.id != False:
                        if l.test != False:
                            if ("#"+str(l.employee_id.parent_id.user_id.id)+"#") not in l.test:
                                l.test = l.test + ("#"+str(l.employee_id.parent_id.user_id.id)+"#")
                        else:
                            l.test = ("#"+str(l.employee_id.parent_id.user_id.id)+"#")
                # position
                if  l2.validators_type == 'position':
                    employees = self.env['hr.employee'].sudo().search([('multi_job_id','in',l2.holiday_validators_position.id)])
                    for employee in employees:
                        if l.test != False:
                            if ("#"+str(employee.user_id.id)+"#") not in l.test:
                                l.test = l.test + ("#"+str(employee.user_id.id)+"#")
                        else:
                            l.test = ("#"+str(employee.user_id.id)+"#")
                #user
                if  l2.validators_type == 'user':
                    if l.test != False:
                        if ("#"+str(l2.holiday_validators_user.id)+"#") not in l.test:
                            l.test = l.test + ("#"+str(l2.holiday_validators_user.id)+"#")
                    else:
                        l.test = ("#"+str(l2.holiday_validators_user.id)+"#")
                if not(l2.approval != True or (l2.approval == True and l2.validation_status == True)): 
                    break                                 
                                                        






