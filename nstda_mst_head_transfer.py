# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from datetime import datetime,timedelta
from openerp.tools.translate import _
from email import _name
from bsddb.dbtables import _columns
from openerp import tools
import re
from openerp import SUPERUSER_ID
from docutils.parsers import null
from openerp.exceptions import except_orm, Warning, RedirectWarning


class nstda_mst_head_transfer(models.Model):

    def _needaction_count(self, cr, uid, domain=None, context=None):
        """ Get the number of actions uid has to perform. """
        dom = []
        if not domain:
            dom = self._needaction_domain_get(cr, uid, context=context)
        else:
            dom = domain

        if not dom:
            return 0
        res = self.search(cr, uid, (domain or []) + dom, limit=100, order='id DESC', context=context)
        return len(res)
    
    
    @api.model
    def create(self, values):
        temp = values['type_docs']
        if temp == "T":
            values['state'] = 'draft'
            values['detail_ids_S'] = False
            values['detail_ids_B'] = False
        elif temp == "B":
            values['state'] = 'draft'
            values['detail_ids_T'] = False
            values['detail_ids_S'] = False
        elif temp == "S":
            values['state'] = 'draft'
            values['detail_ids_T'] = False
            values['detail_ids_B'] = False
            
        seq_code = "nstda.mst"
        obj = self.env['ir.sequence'].search([('code', '=', seq_code)])
        seq = obj.get(seq_code)
        values['doc_no'] =  seq
        res_id = super(nstda_mst_head_transfer, self).create(values)
        return res_id
    
    
    @api.multi
    def write(self, values):
        res_id = super(nstda_mst_head_transfer, self).write(values)    
        return res_id
    
    
    @api.one
    @api.depends('active_ids','context','type_docs','state','boss','stamp_sup_group_id','new_emp_ids','boss_name')
    @api.onchange('type_docs')
    def onchang_detail(self):

        obj = self.env['res.groups'].search([('name', '=', 'Supplies')])    
        self.stamp_sup_group_id = obj.id
        
        obj_user = self.env['nstdamas.employee'].search([('emp_rusers_id','=',self._uid)], limit=1).id
        list_boss = self.env['nstdamas.boss'].get_boss(obj_user)
        i = 1
        try:
            while True:
                if list_boss[i].bss_id.id != False:
                    boss_id = list_boss[i].bss_id.emp_rusers_id.id
                    break
                i+= 1
                if i == 7:
                    break 
            self.boss = boss_id
        except:
            pass
        
        if 'active_ids' in self._context:
            list_index = self._context['active_ids']
            res_asset = self.env['nstda.mst.asset']
            user_changes = []
            for partner in res_asset.browse(list_index):
                user_changes.append((0, 0, {
                                            'asset_ids': partner.id,
                                            'f_old_name': partner.personel_ids.emp_fname_en,
                                            'f_old_location': partner.location_ids.description,
                                            'f_old_room': partner.room,
                                            'f_old_status': partner.asset_status_ids.description,
                                            'f_old_purchasing_method' : partner.purchasing_method_ids.description,
                                            'f_old_name_b': partner.personel_ids.emp_fname_en,
                                            'f_old_location_b': partner.location_ids.description,
                                            'f_old_room_b': partner.room,
                                            'f_old_status_b': partner.asset_status_ids.description,
                                            'f_old_purchasing_method_b': partner.purchasing_method_ids.description,
                                            }))

            if self.type_docs == "T":
                self.detail_ids_T = user_changes
                self.detail_ids_S = user_changes.append((2,partner.id))
                self.detail_ids_B = user_changes.append((2,partner.id))
            elif self.type_docs == "B":
                self.detail_ids_B = user_changes
                self.detail_ids_T = user_changes.append((2,partner.id))
                self.detail_ids_S = user_changes.append((2,partner.id))
            elif self.type_docs == "S":
                self.detail_ids_S = user_changes
                self.detail_ids_T = user_changes.append((2,partner.id))
                self.detail_ids_B = user_changes.append((2,partner.id))
                
            
    @api.one
    @api.depends('stamp_recipient_id','new_emp_ids')
    @api.onchange('stamp_recipient_id','new_emp_ids')
    def get_recip_boss(self):
        list_recip_boss = self.env['nstdamas.boss'].get_boss(self.new_emp_ids.id)
        i = 1
        try:
            while True:
                if list_recip_boss[i].bss_id.id != False:
                    recip_boss_res = list_recip_boss[i].bss_id.emp_rusers_id.id
                    break
                i+= 1
                if i == 7:
                    break
            self.recip_boss = recip_boss_res
        except:
            pass
            
            
    @api.one
    @api.depends('state')
    @api.onchange('state')
    def show_name_state(self):
        try:
            if self.state == 'boss':
                name_state = self.boss
            elif self.state == 'edit' or self.state == 'close':
                name_state = self.create_uid.id
            elif self.state == 'recipient':
                name_state = self.stamp_recipient_id
            elif self.state == 'recip_boss':
                name_state = self.recip_boss

            obj_boss = self.env['nstdamas.employee'].search([('emp_rusers_id','=',name_state)], limit=1)
            boss_fname = obj_boss.emp_fname_en
            boss_lname = obj_boss.emp_lname_en
            name = '%s %s' %(boss_fname, boss_lname)
            self.boss_name = name
        except:
            pass
        
        
    @api.one
    @api.depends('state')
    @api.onchange('state')
    def show_current_wait(self):
        if self.state in ['boss','edit','close','recipient','recip_boss']:
            self.current_wait = self.boss_name
        elif self.state == 'supplies':
            self.current_wait = self.sup_name
        elif self.state == 'supplies_boss':
            self.current_wait = self.sup_bossname
        
        
    @api.one
    @api.depends('stamp_sup_id')
    @api.onchange('stamp_sup_id')
    def show_sup_name(self):
        try:
            get_sup = self.stamp_sup_id.id
            obj_user = self.env['nstdamas.employee'].search([('emp_rusers_id','=',get_sup)])
            sup_fname = obj_user.emp_fname_en
            sup_lname = obj_user.emp_lname_en
            name = '%s %s' %(sup_fname, sup_lname)
            self.sup_name = name
        except:
            pass
    
    
    @api.one
    @api.depends('stamp_boss_sub_id')
    @api.onchange('stamp_boss_sub_id')
    def show_sup_bossname(self):
        try:
            get_sup = self.stamp_boss_sub_id.id
            obj_user = self.env['nstdamas.employee'].search([('emp_rusers_id','=',get_sup)])
            sup_fname = obj_user.emp_fname_en
            sup_lname = obj_user.emp_lname_en
            name = '%s %s' %(sup_fname, sup_lname)
            self.sup_bossname = name
        except:
            pass
        
        
    @api.one
    @api.depends('new_emp_ids')
    @api.onchange('new_emp_ids')
    def stamp_recip_id(self):
        self.stamp_recipient_id = self.new_emp_ids.emp_rusers_id.id
        
        
    @api.one
    @api.depends('stamp_sup_group_id')
    def get_sup_id(self):
        obj_emp = self.env['nstdamas.employee'].search([('emp_rusers_id', '=',self._uid)])
        if obj_emp.emp_org_id.id == 1:
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','003441')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id    
        elif obj_emp.emp_org_id.id == 2:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','002477')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 3:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','001331')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id    
        elif obj_emp.emp_org_id.id == 4:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','000669')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 5:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','001457')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 6:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','004372')])
            self.stamp_sup_id = obj_sup.emp_rusers_id.id
            
            
    @api.one
    @api.depends('stamp_sup_group_id')
    def get_boss_sup_id(self):
        obj_emp = self.env['nstdamas.employee'].search([('emp_rusers_id', '=',self._uid)])
        if obj_emp.emp_org_id.id == 1:
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','002840')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id    
        elif obj_emp.emp_org_id.id == 2:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','001003')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 3:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','000178')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id    
        elif obj_emp.emp_org_id.id == 4:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','000143')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 5:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','000040')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id  
        elif obj_emp.emp_org_id.id == 6:     
            obj_sup = self.env['nstdamas.employee'].search([('emp_id', '=','003696')])
            self.stamp_boss_sub_id = obj_sup.emp_rusers_id.id  
        
        
    @api.one
    @api.depends('cek_groups','stamp_sup_group_id')    
    def _cek_groups(self):
        self.cek_groups = False
        obj_user = self.env['res.users'].search([('id', '=', self._uid)])
        for i in obj_user.groups_id:
            if self.stamp_sup_group_id == i.id:
                self.cek_groups = True
              
                
    @api.one
    @api.depends('state')
    @api.onchange('state')
    def _inv(self):
        if self.state == 'boss':
            if self.boss == self._uid:
                self.inv_b = True
        elif self.state == 'recipient':
            if self.stamp_recipient_id == self._uid:
                self.inv_r = True
        elif self.state == 'recipient_boss':
            if self.recip_boss == self._uid:
                self.inv_rb = True
        elif self.state == 'supplies':
            if self.stamp_sup_id.id == self._uid:
                self.inv_s = True
        elif self.state == 'supplies_boss':
            if self.stamp_boss_sub_id.id == self._uid:
                self.inv_sb = True
        elif self.state == 'edit':
            if self.create_uid.id == self._uid:
                self.inv_c = True
                
                
    @api.one
    @api.onchange('state','detail_ids_T','detail_ids_S','detail_ids_B')
    @api.depends('state','detail_ids_T','detail_ids_S','detail_ids_B')
    def _get_inv(self):
        if self.detail_ids_T:
            self.inv_a = self.detail_ids_T.inv_a
        elif self.detail_ids_S:
            self.inv_a = self.detail_ids_S.inv_a
        elif self.detail_ids_B:
            self.inv_a = self.detail_ids_B.inv_a
        else:
            self.inv_a = False
            
            
    @api.one
    @api.depends('new_emp_ids','borrow_emp_ids')
    @api.onchange('new_emp_ids','borrow_emp_ids')
    def _get_plant_group(self):
        if self.type_docs == "T":
            self.plant_group = self.new_emp_ids.emp_org_id.org_id
        elif self.type_docs == "B":
            self.plant_group = self.borrow_emp_ids.emp_org_id.org_id
        
                                                                                                   
    _name = 'nstda.mst.head.transfer'
    _inherit = ['ir.needaction_mixin']
    _rec_name = 'doc_no'
    
    type_docs = fields.Selection([('T', 'เปลี่ยนผู้ถือครอง'),
                                  ('S', 'เปลี่ยนสถานะ'),
                                  ('B', 'การยืม'),],
                                  'Type', default= 'T'
                                  )
    
    doc_no = fields.Char('Number')
    doc_date = fields.Date('Date', default =fields.Date.today, readonly=True)
    detail_ids_T = fields.One2many('nstda.mst.transfer.detail', 'transfer_head_ids', 'details', domain=[('type_docs', '=', 'T')]) 
    detail_ids_S = fields.One2many('nstda.mst.transfer.detail', 'transfer_head_ids', 'details', domain=[('type_docs', '=', 'S')])
    detail_ids_B = fields.One2many('nstda.mst.transfer.detail', 'transfer_head_ids', 'details', domain=[('type_docs', '=', 'B')])
    new_emp_ids = fields.Many2one('nstdamas.employee','New Employee', domain ="[('emp_ems_id.ems_name_en','like','Active')]", required=False)
    new_location_ids = fields.Many2one('nstda.mst.location','New Location', required=False)
    new_room = fields.Char('New Room', required=False)
    borrow_emp_ids = fields.Many2one('nstdamas.employee','Borrow Employee', domain ="[('emp_ems_id.ems_name_en','like','Active')]", required=False)
    borrow_location_ids = fields.Many2one('nstda.mst.location','Borrow Location', required=False)
    borrow_room = fields.Char('Borrow Room', required=False)
    plant_group = fields.Char('Plant', computer=_get_plant_group)

    state = fields.Selection([('draft', 'Draft'),
            ('send', 'Draft'),
            ('edit', 'Edit'),
            ('boss', 'Boss Approve'),
            ('recipient', 'New Emp. Approve'),
            ('recipient_boss', 'New Emp. Boss Approve'),
            ('supplies', 'S. Approve'),
            ('supplies_boss', 'S. Boss Approve'),
            ('close', 'Done')],
             readonly=True, track_visibility='onchange', default='draft',)
    
    boss = fields.Integer('Boss')
    boss_name = fields.Char('Boss Name', compute = show_name_state)
    current_wait = fields.Char('Name', compute = show_current_wait)
    recip_boss = fields.Integer('Boss Recipient', compute = get_recip_boss, store=True)
    sup_name = fields.Char('Sup Name', compute = show_sup_name, store=True)
    sup_bossname = fields.Char('Sup Name', compute = show_sup_bossname)
    stamp_sup_group_id = fields.Integer('Stamp Sup Group ID') 
    stamp_recipient_id = fields.Integer('Stamp Recipient ID', compute = stamp_recip_id, store=True)
    cek_groups = fields.Boolean('Check UID', compute = '_cek_groups')
    stamp_sup_id = fields.Many2one('res.users','Stamp Sup Id', compute = get_sup_id, store=True)
    stamp_boss_sub_id = fields.Many2one('res.users','Stamp Boss Sup Id', compute = get_boss_sup_id, store=True)
    
    create_uid = fields.Many2one('res.users', 'Created By')
    
    inv_b = fields.Boolean('Inv B', compute = '_inv') 
    inv_r = fields.Boolean('Inv R', compute = '_inv')
    inv_rb = fields.Boolean('Inv RB', compute = '_inv')
    inv_s = fields.Boolean('Inv S', compute = '_inv')
    inv_sb = fields.Boolean('Inv SB', compute = '_inv')
    inv_c = fields.Boolean('Inv C', compute = '_inv')
    inv_a = fields.Boolean('Inv A', compute = '_get_inv')   
    
    @api.one
    def state_draft(self):
        self.state='draft'
        
    
    @api.one
    def state_send(self):
        tmp_state = self.state
        if self.state == 'draft' or self.state == 'edit':
            if self.type_docs == "T" or self.type_docs == "B":
                self.state = 'boss'  
            elif self.type_docs == "S":
                self.state = 'supplies'
        else:
            self.state =tmp_state
            
        
    @api.one
    def state_edit(self):
        if self.boss == self._uid or self.stamp_recipient_id == self._uid or self.recip_boss == self._uid or self.stamp_sup_id.id == self._uid or self.stamp_boss_sub_id.id == self._uid:
            self.state='edit'
        else:
            raise Warning('สำหรับผู้บังคับบัญชาผู้โอน, ผู้รับโอน และเจ้าหน้าที่')
        
         
    @api.one
    def state_boss(self):
        if self.boss == self._uid :
            self.state='recipient'
        else:
            raise Warning('สำหรับผู้บังคับบัญชาผู้โอน')
    
    
    @api.one
    def state_recipient(self):
        if self.stamp_recipient_id == self._uid :
            self.state='recipient_boss'
        else:
            raise Warning('สำหรับผู้รับผู้โอน') 
        
        
    @api.one
    def state_recipient_boss(self):
        if self.recip_boss == self._uid :
            self.state='supplies'
        else:
            raise Warning('สำหรับผู้บังคับบัญชาผู้รับโอน')
        
        
    @api.one
    def state_supplies(self):
        if self.stamp_sup_id.id == self._uid :
            self.state='supplies_boss'
        else:
            raise Warning('สำหรับเจ้าหน้าที่พัสดุ')
    
        
    @api.one
    def state_supplies_boss(self):
        if self.stamp_boss_sub_id.id == self._uid :
            self.state='close'
        else:
            raise Warning('สำหรับหัวหน้าเจ้าหน้าที่พัสดุ')
    
####################################################################################################

class nstda_mst_transfer_detail(models.Model):
    
#     def default_get(self, cr, uid, fields, context=None):
#         if context is None:
#             context = {}
#         res = super(nstda_mst_transfer_detail, self).default_get(cr, uid, fields, context)
#         if context.get('active_model') == 'nstda.mst.asset' and context.get('active_ids'):
#             asset_ids = context['active_ids']
#             res['asset_ids'] = asset_ids
#         return res
        
    @api.one
    @api.depends('asset_ids','f_old_name','f_old_location','temp_old_room'
                 ,'f_old_name_b','f_old_location_b','temp_old_room_b','f_old_status_b','f_old_status_b'
                 ,'transfer_head_ids')
    @api.onchange('asset_ids')
    def onchange_assid_ids(self):

        pro_master_obj = self.env['nstda.mst.asset']
        project_id = pro_master_obj.search([('id', '=', self.asset_ids.id)],limit=1)
        if project_id:
            nstda_project = pro_master_obj.browse(self.asset_ids.id)
                
            self.f_old_name_b = nstda_project.personel_ids.emp_fname_en
            self.f_old_location_b = nstda_project.location_ids.description
            self.f_old_room_b = nstda_project.room 
            self.f_old_status_b = nstda_project.asset_status_ids.description
            self.f_old_purchasing_method_b = nstda_project.purchasing_method_ids.description
            
            self.f_old_name = self.f_old_name_b
            self.f_old_location = self.f_old_location_b   
            self.f_old_room = self.f_old_room_b
            self.f_old_status = self.f_old_status_b
            self.f_old_purchasing_method = self.f_old_purchasing_method_b
                
        else:
            self.f_old_name = False          
            self.f_old_location = False
            self.f_old_room = False
            self.f_old_status = False
            self.f_old_purchasing_method = False
   
   
    @api.one
    @api.depends('f_old_name','f_old_name_b')
    def get_old_em(self):
        self.f_old_name = self.f_old_name_b
        
        
    @api.one
    @api.depends('f_old_location','f_old_location_b')    
    def get_old_lo(self):
        self.f_old_location = self.f_old_location_b
        
        
    @api.one
    @api.depends('f_old_room','f_old_room_b')    
    def get_old_room(self):
        self.f_old_room = self.f_old_room_b       
        
        
    @api.one
    @api.depends('f_old_status','f_old_status_b')    
    def get_old_status(self):
        self.f_old_status = self.f_old_status_b   
        
        
    @api.one
    @api.depends('f_old_purchasing_method','f_old_purchasing_method_b')    
    def get_old_purchasing_method(self):
        self.f_old_purchasing_method = self.f_old_purchasing_method_b       
    
    
    @api.one
    @api.onchange('transfer_head_ids')
    @api.depends('transfer_head_ids')    
    def _get_type(self):  
        self.type_docs =  self.transfer_head_ids.type_docs
        
        
    @api.one
    @api.onchange('transfer_head_ids', 'transfer_head_ids.state')
    @api.depends('transfer_head_ids', 'transfer_head_ids.state')
    def _get_state(self):  
        self.state =  self.transfer_head_ids.state
        

    @api.one
    @api.onchange('state')
    @api.depends('state')
    def _get_inv(self):
        self.inv_b = self.transfer_head_ids.inv_b
        self.inv_r = self.transfer_head_ids.inv_r
        self.inv_rb = self.transfer_head_ids.inv_rb
        self.inv_s = self.transfer_head_ids.inv_s
        self.inv_sb = self.transfer_head_ids.inv_sb
        self.inv_c = self.transfer_head_ids.inv_c
        if self.asset_ids:
            self.inv_a = True
        else:
            self.inv_a = False


    @api.model
    def _getUserId(self):
        return [('personel_ids', '=', self.env['nstdamas.employee'].search([('emp_rusers_id','=',self._uid)]).id)]
    
    
    @api.one
    @api.depends('asset_ids')
    @api.onchange('asset_ids')
    def _get_plant_group(self):
        self.plant_group = self.asset_ids.personel_ids.emp_org_id.org_id

     
    _name = 'nstda.mst.transfer.detail'
                
    transfer_head_ids = fields.Many2one('nstda.mst.head.transfer','Header')
    asset_ids = fields.Many2one('nstda.mst.asset','Asset', domain=_getUserId, required=True)
    new_asset_status_ids = fields.Many2one('nstda.mst.asset.status','Asset Status', domain=[('description', 'in', ['ใช้งานปกติ','ชำรุด','สูญหาย','จำหน่าย - ขาย','จำหน่าย','จำหน่าย - แลกเปลี่ยน','จำหน่าย - โอน','จำหน่าย - แปรสภาพ/ทำลาย','','หมดอายุการใช้งาน']),('status_code', '!=', False)], required=True)
    status = fields.Boolean('Status',default=True)
    create_uid = fields.Many2one('res.users', 'Created By')
    notes = fields.Char('หมายเหตุ', required=True)
    return_bdate = fields.Date('วันที่คืน', required=True)
    new_location_ids = fields.Many2one('nstda.mst.location','New Asset Location', required=True)
    new_room = fields.Char('New Asset Room', required=True)
    plant_group = fields.Char('Plant', computer=_get_plant_group)
    
    f_old_name_b = fields.Char()
    f_old_location_b = fields.Char()
    f_old_room_b = fields.Char()
    f_old_status_b = fields.Char()
    f_old_purchasing_method_b = fields.Char()
    f_old_name = fields.Char('f_old_name',compute = 'get_old_em')
    f_old_location = fields.Char('f_old_location',compute = 'get_old_lo',store=True,)
    f_old_room = fields.Char('f_old_room',compute = 'get_old_room',store=True,)
    f_old_status = fields.Char('f_old_status',compute = 'get_old_status',store=True,)
    f_old_purchasing_method = fields.Char('f_old_purchasing_method',compute = 'get_old_purchasing_method',store=True,)
    
    type_docs = fields.Selection([('T', 'เปลี่ยนผู้ถือครอง'),
                                ('S', 'เปลี่ยนสถานะ'),
                                ('B', 'การยืม'),],
                               'Type', compute='_get_type')
    
    state = fields.Selection([('draft', 'Draft'),
            ('send', 'Draft'),
            ('edit', 'EDIT'),
            ('boss', 'Boss Approve'),
            ('recipient', 'New Emp. Approve'),
            ('recipient_boss', 'New Emp. Boss Approve'),
            ('supplies', 'S. Approve'),
            ('supplies_boss', 'S. Boss Approve'),
            ('close', 'Done')],
             readonly=True, track_visibility='onchange', compute='_get_state' ,store=True, default='draft')
    
    report_doc_no = fields.Char('Number',store=True, related='transfer_head_ids.doc_no')
    report_inventory_no = fields.Char('NSTDA Number', store=False, related='asset_ids.inventory_no')
    report_asset_no = fields.Char('Number Reference', store=True, related='asset_ids.asset_no')
    report_asset_no_sub_number = fields.Char('Sub Number Reference', store=False, related='asset_ids.asset_no_sub_number')
    report_company_code = fields.Char('Company Code', default='NS01', readonly=True)
    report_business_area = fields.Char('Business Area', store=True, related='asset_ids.location_ids.plant')
    report_plant = fields.Char('Plant', store=False, related='asset_ids.location_ids.plant')
    report_purchasing_method = fields.Char('Purchasing Method', store=False, related='asset_ids.purchasing_method_ids.purmenthod_code')
    report_new_location = fields.Char('New Location', store=True, related='transfer_head_ids.new_location_ids.location_code')
    report_new_room = fields.Char('New Room', store=True, related='transfer_head_ids.new_room')
    report_new_emp = fields.Char('New Personal Number', store=True, related='transfer_head_ids.new_emp_ids.emp_id')
    report_old_location = fields.Char('Location', store=False, related='asset_ids.location_ids.location_code')
    report_old_room = fields.Char('Room', store=False, related='asset_ids.room')
    report_personal = fields.Char('Personal Number', store=True, related='asset_ids.personel_ids.emp_id')
    report_old_status = fields.Char('Asset Status', store=False, related='asset_ids.asset_status_ids.status_code')
    report_new_asset_status = fields.Char('New Asset Status', store=True, related='new_asset_status_ids.status_code')
    report_type_docs = fields.Selection([('T', 'เปลี่ยนผู้ถือครอง'),
                                ('S', 'เปลี่ยนสถานะ'),
                                ('B', 'การยืม'),],
                               'Type', store=False, related='transfer_head_ids.type_docs')
    
    inv_b = fields.Boolean('Inv B', compute = '_get_inv') 
    inv_r = fields.Boolean('Inv R', compute = '_get_inv')
    inv_rb = fields.Boolean('Inv RB', compute = '_get_inv')
    inv_s = fields.Boolean('Inv S', compute = '_get_inv')
    inv_sb = fields.Boolean('Inv SB', compute = '_get_inv')
    inv_c = fields.Boolean('Inv C', compute = '_get_inv')
    inv_a = fields.Boolean('Inv A', compute = '_get_inv', default=False)