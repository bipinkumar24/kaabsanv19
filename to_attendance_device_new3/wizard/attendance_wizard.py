import logging
from datetime import datetime
import pytz
# from datetime import timedelta
from datetime import date, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

from datetime import datetime, time
class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    @api.model
    def _get_all_device_ids(self):
        all_devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        if all_devices:
            return all_devices.ids
        else:
            return []

    set_date = fields.Date(string='Sync Date From',
                           default=lambda self: fields.Date.to_string(date.today() - timedelta(days=1)))
    set_date_to = fields.Date(string='Sync Date To', default=date.today())
    time_date = fields.Datetime(string='Download from',
                                default=lambda self: fields.Date.to_string(datetime.today() - timedelta(days=1)))
    device_ids = fields.Many2many('attendance.device', string='Devices', default=_get_all_device_ids,
                                  domain=[('state', '=', 'confirmed')])
    fix_attendance_valid_before_synch = fields.Boolean(string='Fix Attendance Valid',
                                                       help="If checked, Odoo will recompute all attendance data for their valid"
                                                            " before synchronizing with HR Attendance (upon you hit the 'Synchronize Attendance' button)")

    def download_attendance_manually(self):
        # TODO: remove me after 12.0
        self.action_download_attendance()

    def action_download_attendance(self):
        if not self.device_ids:
            raise UserError(_('You must select at least one device to continue!'))
        self.device_ids.action_attendance_download()

    def download_device_attendance(self):
        # TODO: remove me after 12.0
        self.cron_download_device_attendance()

    def cron_download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        for i in devices:
            print(devices, 'tryyyyyyyyyyy')

            try:
                zk = i.connect()
                if zk:
                    zk.connect()

                    i.enableDevice()
                    i.disableDevice()
                    i.action_attendance_download_auto()
                else:
                    print('doubl fail')

            except:
                print("Fail")
                pass

    def cron_sync_attendance(self):
        print('self.with_context(synch_ignore_constraints=True).sync_attendance()')
        # self.with_context(synch_ignore_constraints=True).sync_attendance()
        self.download_attendance_custom_auto()
    #

    def _get_shift_for_check_in(self, check_in_minutes, first_shift, second_shift, third_shift, attendance_id):
        """
        Helper function to check which shift the check-in time falls into.
        Compares the check-in time (in minutes) with shift times (also in minutes).
        Returns the matching shift or None if no match is found.
        """
        # Convert shift start and end times to minutes
        first_shift_start = self._time_to_minutes(first_shift.hh_from, first_shift.mm_from)
        first_shift_end = self._time_to_minutes(first_shift.hh_to, first_shift.mm_to)
        
        second_shift_start = self._time_to_minutes(second_shift.hh_from, second_shift.mm_from)
        second_shift_end = self._time_to_minutes(second_shift.hh_to, second_shift.mm_to)
        
        third_shift_start = self._time_to_minutes(third_shift.hh_from, third_shift.mm_from)
        third_shift_end = self._time_to_minutes(third_shift.hh_to, third_shift.mm_to)
        
        # Compare the check-in time with shift times
        if first_shift_start <= check_in_minutes <= first_shift_end:
            if third_shift_start <= check_in_minutes <= third_shift_end and attendance_id.employee_id.id in third_shift.employees.ids:
                return third_shift
            return first_shift
        if second_shift_start <= check_in_minutes <= second_shift_end:
            if third_shift_start <= check_in_minutes <= third_shift_end and attendance_id.employee_id.id in third_shift.employees.ids:
                return third_shift
            return second_shift
        elif third_shift_start <= check_in_minutes <= third_shift_end:
            return third_shift
        print("helllo")
        return False

    def _get_shift_for_check_in_out(self, check_in_minutes, check_out_minutes, first_shift, second_shift, third_shift, attendance_id):
        """
        Helper function to check which shift the check-in and check-out times fall into.
        Compares the check-in time (in minutes) and check-out time (in minutes) with shift times (also in minutes).
        Returns the matching shift if both check-in and check-out are within the same shift, or None if no match is found.
        """
        # Convert shift start and end times to minutes
        first_shift_start = self._time_to_minutes(first_shift.hh_from, first_shift.mm_from)
        first_shift_end = self._time_to_minutes(first_shift.hh_to, first_shift.mm_to)
        
        second_shift_start = self._time_to_minutes(second_shift.hh_from, second_shift.mm_from)
        second_shift_end = self._time_to_minutes(second_shift.hh_to, second_shift.mm_to)
        
        third_shift_start = self._time_to_minutes(third_shift.hh_from, third_shift.mm_from)
        third_shift_end = self._time_to_minutes(third_shift.hh_to, third_shift.mm_to)

        # Check if both check-in and check-out are within the same shift and if the employee is valid
        if first_shift_start <= check_in_minutes <= first_shift_end and first_shift_start <= check_out_minutes <= first_shift_end:
            if third_shift_start <= check_in_minutes <= third_shift_end and third_shift_start <= check_out_minutes <= third_shift_end and attendance_id.employee_id.id in third_shift.employees.ids:
                return third_shift
            if attendance_id.employee_id.id in first_shift.employees.ids:
                return first_shift
        elif second_shift_start <= check_in_minutes <= second_shift_end and second_shift_start <= check_out_minutes <= second_shift_end:
            if third_shift_start <= check_in_minutes <= third_shift_end and third_shift_start <= check_out_minutes <= third_shift_end and attendance_id.employee_id.id in third_shift.employees.ids:
                return third_shift
            return second_shift
        elif third_shift_start <= check_in_minutes <= third_shift_end and third_shift_start <= check_out_minutes <= third_shift_end:
            return third_shift

        return False  # If no shift matches both check-in and check-out times
    

    def check_shift_data(self, attendance_id, first_shift, second_shift, third_shift):
        # Initialize the variables
        valid = False
        shift_id = None
        local_tz = pytz.timezone('Asia/Kolkata')
        
        # Check if check_in exists
        print(attendance_id)
        if attendance_id.check_in and not attendance_id.check_out:
            check_in = attendance_id.check_in
            local_time = check_in.astimezone(local_tz)
            check_in_minutes = self._time_to_minutes(local_time.hour, local_time.minute)
            
            # Determine the valid shift based on check-in time
            shift_id = self._get_shift_for_check_in(check_in_minutes, first_shift, second_shift, third_shift, attendance_id)
            
            if shift_id and attendance_id.employee_id.id in shift_id.employees.ids:
                valid = True

        if attendance_id.check_in and attendance_id.check_out:
            check_in = attendance_id.check_in
            local_time = check_in.astimezone(local_tz)
            local_time_check_out = attendance_id.check_out.astimezone(local_tz)
            check_in_minutes = self._time_to_minutes(local_time.hour, local_time.minute)
            check_out_minutes = self._time_to_minutes(local_time_check_out.hour, local_time_check_out.minute)

            # Determine the valid shift based on check-in time
            shift_id = self._get_shift_for_check_in_out(check_in_minutes, check_out_minutes, first_shift, second_shift, third_shift, attendance_id)

            if shift_id and attendance_id.employee_id.id in shift_id.employees.ids:
                valid = True

        return shift_id, valid

    def _time_to_minutes(self, hours, minutes):
        """
        Helper function to convert hours and minutes to minutes since midnight.
        """
        return hours * 60 + minutes

    def _is_create_attednace(self, atten_time, second_shift, first_shift):
        is_create = False
        local_tz = pytz.timezone('Asia/Kolkata')
        local_time = atten_time.astimezone(local_tz)
        check_in_minutes = self._time_to_minutes(local_time.hour, local_time.minute)

        first_shift_start = self._time_to_minutes(first_shift.hh_from, first_shift.mm_from)
        second_shift_end = self._time_to_minutes(second_shift.hh_to, second_shift.mm_to)

        if first_shift_start <= check_in_minutes <= second_shift_end:
            is_create = True
        else:
            is_create = False
        return is_create

    def _is_update_old_attdance(self, attendance_id, attendance_time):
        is_update = False
        local_tz = pytz.timezone('Asia/Kolkata')
        local_time = attendance_time.astimezone(local_tz)
        check_in_minutes = self._time_to_minutes(local_time.hour, local_time.minute)

        shift_end = self._time_to_minutes(attendance_id.shift_id.hh_to, attendance_id.shift_id.mm_to)

        if check_in_minutes <= shift_end:
            is_update = True
        else:
            is_update = False
        return is_update

    def is_updated_today(self, attendance_id, attendance_time):
        # Default to False
        is_update = False
        
        if attendance_id and attendance_id.check_in:
            # Ensure the time zone conversion is based on 'Asia/Kolkata'
            local_tz = pytz.timezone('Asia/Kolkata')
            
            # Convert check-in time to local time (Asia/Kolkata)
            local_check_in_time = attendance_id.check_in.astimezone(local_tz)
            
            # Extract the date part of check-in time
            check_in_date = local_check_in_time.date()
            
            # Get today's date in the local timezone (Asia/Kolkata)
            today_checkin = attendance_time.astimezone(local_tz)
            today = today_checkin.date()
            
            # Compare the local check-in date with today's date
            if check_in_date == today:
                is_update = True

        return is_update

    def download_attendance_custom(self):
        synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)
        att_obj = self.env['hr.attendance'].sudo()
        user = self.env['attendance.device.user'].search([('employee_id', '!=', False)])
        N_DeviceUserAttendance = self.env['user.attendance'].sudo()
        first_shift = self.env['ti.shift.management'].search([('code','=','First')], limit=1)
        second_shift = self.env['ti.shift.management'].search([('code','=','Second')], limit=1)
        third_shift = self.env['ti.shift.management'].search([('code','=','Third')], limit=1)
        for n in range(1):
            n_unsync_data = N_DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                                                           ('employee_id', '!=', False), ('valid', '=', True),
                                                           ('date', '>=', self.set_date),('date','<=',self.set_date_to)

                                                           ], order='timestamp ASC')
            print(len(n_unsync_data), "dddddddsssssssssssddddddddddddddddddddddddddddddddddd")
            for each in n_unsync_data:
                atten_time = each.timestamp
                somalia_tz = pytz.timezone('Africa/Mogadishu')
                local_tz = pytz.timezone('Asia/Kolkata')
                atten_time1 = atten_time.astimezone(somalia_tz)
                atten_time1 = datetime.strftime(atten_time1, '%Y-%m-%d %H:%M:%S')
                atten_time1 = datetime.strptime(atten_time1, '%Y-%m-%d %H:%M:%S')
                _logger.info(f"{each.employee_id.name}///{atten_time1}//{atten_time}")
                for uid in user:
                    if uid.user_id == each.employee_id.barcode:
                        get_user_id = uid.employee_id.id
                        if get_user_id:
                            duplicate_atten_ids = att_obj.search(
                                [('employee_id', '=', get_user_id), ('check_in', '=', atten_time)])
                            if duplicate_atten_ids:
                                continue
                            else:
                                att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                          ("check_out", "=", False)], order='id desc', limit=1)

                                print(att_var,"dooooooooooooooooooooossssssssssssssssssssssssssssssssssssssssssssssssss")
                                if att_var:
                                    if len(att_var) == 2:
                                        att_var = att_var[0]
                                is_update_today = self.is_updated_today(att_var, atten_time)
                                if not att_var:
                                    is_create = self._is_create_attednace(atten_time, second_shift, first_shift)
                                    # rec.checkin_date = new_checkin
                                    print(is_create, ";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
                                    if is_create:
                                        sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id,date_checkin)VALUES(%s,%s,%s,%s)"
                                        self.env.cr.execute(sql,
                                                            (get_user_id, atten_time, each.device_id.id, atten_time.date()))
                                        id_checkin = att_obj.search(
                                            [('employee_id', '=', get_user_id)
                                             ], limit=1, order='id desc')
                                        re_shift_id, re_valid = self.check_shift_data(id_checkin, first_shift, second_shift, third_shift)
                                        if re_valid:
                                            yu_is_valid = 'y'
                                        else:
                                            yu_is_valid = 'n'
                                        id_checkin.write({'shift_id': re_shift_id.id if re_shift_id else False , 'is_valid': yu_is_valid})
                                        sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql,(id_checkin.id,each.id))
                                        self.env.cr.commit()
                                    else:
                                        continue
                                if len(att_var) == 1:
                                    if att_var.check_in < atten_time:
                                        print("uuuuuuuuuuuuuuuuuuuuuuuuu")
                                        is_update_attednace = self._is_update_old_attdance(att_var, atten_time)
                                        is_update_today = self.is_updated_today(att_var, atten_time)
                                        print(is_update_attednace, is_update_today, "0000000000002222222222222222")
                                        if is_update_attednace and is_update_today:
                                            work_hours = atten_time - att_var.check_in
                                            worked_hours = work_hours.total_seconds() / 3600.0
                                            sql = ("UPDATE hr_attendance SET check_out=%s , checkout_device_id=%s,worked_hours=%s WHERE id=%s")
                                            update_employee_id = self.env.cr.execute(sql, (atten_time, each.device_id.id,worked_hours,att_var.id))
                                            sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                            self.env.cr.execute(sql, (att_var.id, each.id))
                                            self.env.cr.commit()
                                            re_shift_id, re_valid = self.check_shift_data(att_var, first_shift, second_shift, third_shift)
                                            if re_valid:
                                                yu_is_valid = 'y'
                                            else:
                                                yu_is_valid = 'n'
                                            att_var.write({'shift_id': re_shift_id.id if re_shift_id else False, 'is_valid': yu_is_valid})
                                        else:
                                            is_create = self._is_create_attednace(atten_time, second_shift, first_shift)
                                            print(is_create, "444444444444444444444444444444444")
                                            if is_create:
                                                sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id,date_checkin)VALUES(%s,%s,%s,%s)"
                                                self.env.cr.execute(sql,
                                                                    (get_user_id, atten_time, each.device_id.id, atten_time.date()))
                                                id_checkin = att_obj.search(
                                                    [('employee_id', '=', get_user_id)
                                                     ], limit=1, order='id desc')
                                                re_shift_id, re_valid = self.check_shift_data(id_checkin, first_shift, second_shift, third_shift)
                                                if re_valid:
                                                    yu_is_valid = 'y'
                                                else:
                                                    yu_is_valid = 'n'
                                                id_checkin.write({'shift_id': re_shift_id.id if re_shift_id else False , 'is_valid': yu_is_valid})
                                                sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                                self.env.cr.execute(sql,(id_checkin.id,each.id))
                                                self.env.cr.commit()
                    else:
                        pass



    def download_attendance_custom_auto(self):
        first_shift = self.env['ti.shift.management'].search([('code','=','First')], limit=1)
        second_shift = self.env['ti.shift.management'].search([('code','=','Second')], limit=1)
        third_shift = self.env['ti.shift.management'].search([('code','=','Third')], limit=1)
        synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)

        att_obj = self.env['hr.attendance'].sudo()
        user = self.env['attendance.device.user'].sudo().search([('employee_id', '!=', False)])

        N_DeviceUserAttendance = self.env['user.attendance'].sudo()

        first_shift = self.env['ti.shift.management'].search([('name', '=', 'First Shift')])
        second_shift = self.env['ti.shift.management'].search([('name', '=', 'Second Shift')])
        all_shift = self.env['ti.shift.management'].search([], order='number ASC')



        for n in range(1):
            set_date =  (date.today() - timedelta(days=1))
            set_date_to =  date.today()
            print(set_date,set_date_to)
            n_unsync_data = N_DeviceUserAttendance.search([('hr_attendance_id', '=', False),
                                                           ('employee_id', '!=', False), ('valid', '=', True),
                                                           ('date', '>=', set_date),('date','<=',set_date_to)

                                                           ], order='timestamp ASC')
            print(len(n_unsync_data),'/////////')

            # for each in n_unsync_data:

            for each in n_unsync_data:
                atten_time = each.timestamp
                somalia_tz = pytz.timezone('Africa/Mogadishu')
                local_tz = pytz.timezone('Asia/Kolkata')
                atten_time1 = atten_time.astimezone(somalia_tz)
                atten_time1 = datetime.strftime(atten_time1, '%Y-%m-%d %H:%M:%S')
                atten_time1 = datetime.strptime(atten_time1, '%Y-%m-%d %H:%M:%S')
                _logger.info(f"{each.employee_id.name}///{atten_time1}//{atten_time}")
                for uid in user:
                    if uid.user_id == each.employee_id.barcode:
                        get_user_id = uid.employee_id.id
                        if get_user_id:
                            duplicate_atten_ids = att_obj.search(
                                [('employee_id', '=', get_user_id), ('check_in', '=', atten_time)])
                            if duplicate_atten_ids:
                                continue
                            else:
                                att_var = att_obj.search([("employee_id", "=", get_user_id),
                                                          ("check_out", "=", False)], order='id desc', limit=1)

                                print(att_var,"dooooooooooooooooooooossssssssssssssssssssssssssssssssssssssssssssssssss")
                                if att_var:
                                    if len(att_var) == 2:
                                        att_var = att_var[0]
                                is_update_today = self.is_updated_today(att_var, atten_time)
                                if not att_var:
                                    is_create = self._is_create_attednace(atten_time, second_shift, first_shift)
                                    # rec.checkin_date = new_checkin
                                    print(is_create, ";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
                                    if is_create:
                                        sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id,date_checkin)VALUES(%s,%s,%s,%s)"
                                        self.env.cr.execute(sql,
                                                            (get_user_id, atten_time, each.device_id.id, atten_time.date()))
                                        id_checkin = att_obj.search(
                                            [('employee_id', '=', get_user_id)
                                             ], limit=1, order='id desc')
                                        re_shift_id, re_valid = self.check_shift_data(id_checkin, first_shift, second_shift, third_shift)
                                        if re_valid:
                                            yu_is_valid = 'y'
                                        else:
                                            yu_is_valid = 'n'
                                        id_checkin.write({'shift_id': re_shift_id.id if re_shift_id else False , 'is_valid': yu_is_valid})
                                        sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                        self.env.cr.execute(sql,(id_checkin.id,each.id))
                                        self.env.cr.commit()
                                    else:
                                        continue
                                if len(att_var) == 1:
                                    if att_var.check_in < atten_time:
                                        print("uuuuuuuuuuuuuuuuuuuuuuuuu")
                                        is_update_attednace = self._is_update_old_attdance(att_var, atten_time)
                                        is_update_today = self.is_updated_today(att_var, atten_time)
                                        print(is_update_attednace, is_update_today, "0000000000002222222222222222")
                                        if is_update_attednace and is_update_today:
                                            work_hours = atten_time - att_var.check_in
                                            worked_hours = work_hours.total_seconds() / 3600.0
                                            sql = ("UPDATE hr_attendance SET check_out=%s , checkout_device_id=%s,worked_hours=%s WHERE id=%s")
                                            update_employee_id = self.env.cr.execute(sql, (atten_time, each.device_id.id,worked_hours,att_var.id))
                                            sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                            self.env.cr.execute(sql, (att_var.id, each.id))
                                            self.env.cr.commit()
                                            re_shift_id, re_valid = self.check_shift_data(att_var, first_shift, second_shift, third_shift)
                                            if re_valid:
                                                yu_is_valid = 'y'
                                            else:
                                                yu_is_valid = 'n'
                                            att_var.write({'shift_id': re_shift_id.id if re_shift_id else False, 'is_valid': yu_is_valid})
                                        else:
                                            is_create = self._is_create_attednace(atten_time, second_shift, first_shift)
                                            print(is_create, "444444444444444444444444444444444")
                                            if is_create:
                                                sql = "INSERT INTO hr_attendance(employee_id,check_in,checkin_device_id,date_checkin)VALUES(%s,%s,%s,%s)"
                                                self.env.cr.execute(sql,
                                                                    (get_user_id, atten_time, each.device_id.id, atten_time.date()))
                                                id_checkin = att_obj.search(
                                                    [('employee_id', '=', get_user_id)
                                                     ], limit=1, order='id desc')
                                                re_shift_id, re_valid = self.check_shift_data(id_checkin, first_shift, second_shift, third_shift)
                                                if re_valid:
                                                    yu_is_valid = 'y'
                                                else:
                                                    yu_is_valid = 'n'
                                                id_checkin.write({'shift_id': re_shift_id.id if re_shift_id else False , 'is_valid': yu_is_valid})
                                                sql = ("UPDATE user_attendance SET hr_attendance_id=%s WHERE id=%s")
                                                self.env.cr.execute(sql,(id_checkin.id,each.id))
                                                self.env.cr.commit()
                    else:
                        pass


    # def sync_attendance(self):
    #     """
    #     This method will synchronize all downloaded attendance data with Odoo attendance data.
    #     It do not download attendance data from the devices.
    #     """
    #     if self.fix_attendance_valid_before_synch:
    #         self.action_fix_user_attendance_valid()
    #
    #     synch_ignore_constraints = self.env.context.get('synch_ignore_constraints', False)
    #
    #     error_msg = {}
    #     HrAttendance = self.env['hr.attendance'].with_context(synch_ignore_constraints=synch_ignore_constraints)
    #     attendance = self.env['hr.attendance']
    #     activity_ids = self.env['attendance.activity'].search([])
    #
    #     DeviceUserAttendance = self.env['user.attendance']
    #
    #     last_employee_attendance = {}
    #     for activity_id in activity_ids:
    #         if activity_id.id not in last_employee_attendance.keys():
    #             last_employee_attendance[activity_id.id] = {}
    #
    #         unsync_data = DeviceUserAttendance.search([('hr_attendance_id', '=', False),
    #                                                    ('valid', '=', True),
    #                                                    ('employee_id', '!=', False),
    #                                                    ('activity_id', '=', activity_id.id)], order='timestamp ASC')
    #
    #         for att in unsync_data:
    #             employee_id = att.user_id.employee_id
    #             if employee_id.id not in last_employee_attendance[activity_id.id].keys():
    #                 last_employee_attendance[activity_id.id][employee_id.id] = False
    #
    #             if att.type == 'checkout':
    #                 # find last attendance
    #                 last_employee_attendance[activity_id.id][employee_id.id] = HrAttendance.search(
    #                     [('employee_id', '=', employee_id.id),
    #                      ('activity_id', 'in', (activity_id.id, False)),
    #                      ('check_in', '<=', att.timestamp)], limit=1, order='check_in DESC')
    #
    #                 hr_attendance_id = last_employee_attendance[activity_id.id][employee_id.id]
    #
    #                 if hr_attendance_id:
    #                     try:
    #                         hr_attendance_id.with_context(synch_ignore_constraints=synch_ignore_constraints).write({
    #                             'check_out': att.timestamp,
    #                             'checkout_device_id': att.device_id.id
    #                         })
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._get_new_current_checkin()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._plan_attendance()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._late_emp_hours()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._overtime_emp_hour()
    #                         hr_attendance_id.with_context(
    #                             synch_ignore_constraints=synch_ignore_constraints)._get_new_current_checkout()
    #                     except ValidationError as e:
    #                         if att.device_id not in error_msg:
    #                             error_msg[att.device_id] = ""
    #
    #                         msg = ""
    #                         att_check_time = fields.Datetime.context_timestamp(att, att.timestamp)
    #                         msg += str(e) + "<br />"
    #                         msg += _("'Check Out' time cannot be earlier than 'Check In' time. Debug information:<br />"
    #                                  "* Employee: <strong>%s</strong><br />"
    #                                  "* Type: %s<br />"
    #                                  "* Attendance Check Time: %s<br />") % (
    #                                    employee_id.name, att.type, fields.Datetime.to_string(att_check_time))
    #                         _logger.error(msg)
    #                         error_msg[att.device_id] += msg
    #             else:
    #                 # create hr attendance data
    #                 vals = {
    #                     'employee_id': employee_id.id,
    #                     'check_in': att.timestamp,
    #                     'checkin_device_id': att.device_id.id,
    #                     'activity_id': activity_id.id,
    #                 }
    #                 hr_attendance_id = HrAttendance.search([
    #                     ('employee_id', '=', employee_id.id),
    #                     ('check_in', '=', att.timestamp),
    #                     ('checkin_device_id', '=', att.device_id.id),
    #                     ('activity_id', '=', activity_id.id)], limit=1)
    #                 if not hr_attendance_id:
    #                     try:
    #                         hr_attendance_id = HrAttendance.create(vals)
    #                     except Exception as e:
    #                         _logger.error(e)
    #
    #             if hr_attendance_id:
    #                 att.write({
    #                     'hr_attendance_id': hr_attendance_id.id
    #                 })
    #
    #     if bool(error_msg):
    #         for device in error_msg.keys():
    #
    #             if not device.debug_message:
    #                 continue
    #             device.message_post(body=error_msg[device])

    def clear_attendance(self):
        if not self.device_ids:
            raise (_('You must select at least one device to continue!'))
        if not self.env.user.has_group('hr_attendance.group_hr_attendance_manager'):
            raise UserError(_('Only HR Attendance Managers can manually clear device attendance data'))

        for device in self.device_ids:
            device.clearAttendance()

    def action_fix_user_attendance_valid(self):
        all_attendances = self.env['user.attendance'].search([])
        for attendance in all_attendances:
            if attendance.is_valid():
                attendance.write({'valid': True})
            else:
                attendance.write({'valid': False})
