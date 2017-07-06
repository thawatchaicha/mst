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


class nstda_mst_resgroups(models.Model):
    
    _name = 'nstda.mst.resgroups'

####################################################################################################

class res_groups(models.Model):
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            try:
                get_dpm_name = self.env['nstdamas.department'].search([('dpm_id', '=',inv.comment[3:])])
                if get_dpm_name.dpm_cct_id:
                    get_cct_code = self.env['nstdamas.costcenter'].search([('id', '=',get_dpm_name.dpm_cct_id.id)]).cct_id
                else:
                    get_cct_code = self.env['nstdamas.costcenter'].search([('cct_name', '=',get_dpm_name)]).cct_id
            except:
                get_cct_code = False
            if inv.name and get_cct_code:
                result.append((inv.id, "%s - %s" % (inv.name or '', get_cct_code or '')))
            elif inv.comment and inv.name:
                result.append((inv.id, "%s - %s" % (inv.name or '', inv.comment or '')))
            else:
                result.append((inv.id, "%s" % (inv.name or '')))
        return result
    
    _name = 'res.groups'
    _inherit = 'res.groups'
    _rec_name = 'full_name'
    
    full_name = fields.Char(string='full_name', readonly=True, compute=name_get, store=False)

####################################################################################################

class nstdamas_costcenter(models.Model):
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.cct_id and inv.cct_name:
                result.append((inv.id, "%s - %s" % (inv.cct_id or '', inv.cct_name or '')))
            elif inv.comment:
                result.append((inv.id, "%s" % (inv.cct_id or '')))
            elif inv.name:
                result.append((inv.id, "%s" % (inv.cct_name or '')))
        return result
    
    _name = 'nstdamas.costcenter'
    _inherit = 'nstdamas.costcenter'
    _rec_name = 'full_name'
    _order = 'cct_id ASC'
    
    full_name = fields.Char(string='full_name', readonly=True, compute=name_get, store=False)
    
####################################################################################################

class nstdamas_org(models.Model):
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.org_id and inv.org_shortname:
                result.append((inv.id, "%s - %s" % (inv.org_id or '', inv.org_shortname or '')))
            elif inv.org_id:
                result.append((inv.id, "%s" % (inv.org_id or '')))
            elif inv.org_shortname:
                result.append((inv.id, "%s" % (inv.org_shortname or '')))
        return result
    
    _name = 'nstdamas.org'
    _inherit = 'nstdamas.org'
    _rec_name = 'full_name'
    
    full_name = fields.Char(string='full_name', readonly=True, compute=name_get, store=False)

####################################################################################################

class nstda_mst_asset(models.Model):
    
    @api.one
    @api.depends('fiscal_year', 'user_life')
    def _get_use_life(self):
        start = self.fiscal_year
        now = datetime.now()
        if  start != False:
            d1 = int(now.year)- int(start)               
            self.user_life = str(d1)
        else:
            self.user_life = None
           
            
    @api.one
    @api.depends('personel_ids','stamp_res_user_id')
    def stamp_ruser_id(self):
        self.stamp_res_user_id = self.personel_ids.emp_rusers_id.id
        
        
    @api.one
    @api.depends('personel_ids','stamp_user_division')
    def stamp_division(self):
        dvs_id_T ='DIV%s' % self.personel_ids.emp_dvs_id.dvs_id    
        obj = self.env['res.groups'].search([('comment', '=', dvs_id_T)])
        self.stamp_user_division = obj.id
        
    
    @api.multi   
    @api.depends('location_ids','personel_ids')
    @api.onchange('location_ids','personel_ids')
    def _stamp_org_id(self):
        if self.location_ids.plant != False:
            org_code = self.location_ids.plant
            org_id_T = self.env['nstdamas.org'].search([('org_id', '=', org_code)]).id
            self.stamp_org_id = org_id_T
            
            
    @api.one
    def stamp_division_for_search(self):
        self.division_for_search = self.personel_ids.emp_dvs_id.dvs_name
        
        
    @api.one
    def stamp_department_for_search(self):
        self.department_for_search = self.personel_ids.emp_dpm_id.dpm_name
        
        
    @api.model
    def _search_division(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return ['|',
                ('personel_ids.emp_dvs_id.dvs_name', operator, value),
                ('personel_ids.emp_dvs_id.dvs_name_en', operator, value)]
    
    
    @api.model
    def _search_department(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return ['|',
                ('personel_ids.emp_dpm_id.dpm_name', operator, value),
                ('personel_ids.emp_dvs_id.dpm_name_en', operator, value)]
    
    
#     @api.v7  
#     def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
#         if context is None:
#             context = {}
#         res = super(nstda_mst_asset, self).read(cr, uid, ids, fields=fields, context=context, load=load)
#         idx = 0
#         obj_uid = self.pool.get('nstdamas.employee').search(cr,uid,[('emp_rusers_id', '=',  str(uid))])
#         emp_obj = self.pool.get('nstdamas.employee').browse(cr,uid,obj_uid)
#         for r in res:
#             if  r['personel_ids'] != False:
#                 cr_obj = self.pool.get('nstdamas.employee').browse(cr,uid, r['personel_ids'][0])
#                 if r.has_key('division_flag_filter'):
#                     if cr_obj.emp_dvs_id.id != emp_obj.emp_dvs_id.id:
#                         r['division_flag_filter'] = uid
#                 if r.has_key('department_flag_filter'):
#                     if cr_obj.emp_dpm_id.id != emp_obj.emp_dpm_id.id:
#                         r['department_flag_filter'] = uid
#                 # replace line above with replacement value from external database
#             res[idx] = r
#             idx = idx + 1
#              
#         return res    

    _name = 'nstda.mst.asset'
    _rec_name = 'description_1'
                
    asset_no = fields.Char('Number Reference',size = 12,required=True)
    asset_no_sub_number = fields.Char('Sub Number Reference',size = 12)
    inventory_no = fields.Char('NSTDA Number',size = 25)
    description_1 = fields.Char('Description 1',size = 50)
    asset_class = fields.Many2one('nstda.mst.asset.class','Asset Class')
    serial_no = fields.Char('Serial Number',size = 50)
    last_inventory_on = fields.Date('Last Inventory on')
    capitalized_on = fields.Date('Capitalized on')
    first_acquistion_on = fields.Date('First Acquistion On')
    fiscal_year = fields.Char('Fiscal Year',size = 4)
    deactuvation_on = fields.Date('Deactuvation On.')
    cost_center_ids = fields.Many2one('nstdamas.costcenter','Cost Center')
    location_ids = fields.Many2one('nstda.mst.location','Location')
    room = fields.Char('Room',size=20)
    personel_ids = fields.Many2one('nstdamas.employee','Employee',required=True)
    funds_center = fields.Char('Funds Center',size=6)
    wbs_ids = fields.Many2one('nstdamas.project','โครงการ (WBS)', order='prj_id ASC')
    internal_order_ids = fields.Many2one('nstda.mst.internal.order','ใบสั่งงาน (IO)')
    asset_status_ids = fields.Many2one('nstda.mst.asset.status','Asset Status')
    purchasing_method_ids = fields.Many2one('nstda.mst.purchasing.method','Purchasing Method')
    vendor_ids = fields.Many2one('nstda.mst.vendor','Vendor') 
    user_life = fields.Char(compute='_get_use_life', string='Useful Life(Year)',type='Char', method=True ,store=True)  
    
#     mst_files_ids = fields.One2many('ir.attachment', 'res_id', ' ', domain=[], ondelete='cascade')
    
    stamp_res_user_id = fields.Integer('Stamp Res User ID',compute = stamp_ruser_id,store=True)
    group_division_ids = fields.Many2one('res.groups','Group Division')
    group_department_ids = fields.Many2one('res.groups','Group Department')
    stamp_org_id = fields.Many2one('nstdamas.org','ศูนย์',compute = _stamp_org_id,store=True)
    org_groups_id = fields.Many2one('res.groups', ondelete='set null', string="Org Group", domain=[('comment', 'in', ['ORG01', 'ORG02', 'ORG03', 'ORG04', 'ORG05', 'ORG06'])], readonly=True)
    
    division_for_search = fields.Char('Stamp User Division For Search',
                                      compute = stamp_division_for_search, search=_search_division)
    department_for_search = fields.Char('Stamp User Department For Search',
                                        compute = stamp_department_for_search, search=_search_department)
    
    mst_asset_file_ids = fields.One2many('ir.attachment', 'res_id', ' ', domain=[('res_model', '=', 'nstda.mst.asset')], ondelete='cascade', limit=2)
    
    _order = 'description_1 ASC,fiscal_year ASC'
    
    
    @api.model
    def create(self, values):
        values = self.env['ir.attachment'].set_res_model(values, self._name, 'mst_asset_file_ids')
        res_id = super(nstda_mst_asset, self).create(values)
        return res_id


    @api.multi
    def write(self, values):
        values = self.env['ir.attachment'].set_res_model(values, self._name, 'mst_asset_file_ids')
        res_id = super(nstda_mst_asset, self).write(values)
        return res_id
    
####################################################################################################

class nstda_mst_cost_center(models.Model):
    
    _name = 'nstda.mst.cost.center'
    _rec_name = 'description'
    
    business_area = fields.Char('Business Area')
    plan = fields.Char('Plan')  
    cost_center = fields.Char('Cost Center',size=6)  
    fund_center = fields.Char('Fund Center')  
    description = fields.Char('Description',size=50)  
    cost_emp_ids = fields.Many2many('res.users')
    
    _order = 'cost_center ASC'
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.cost_center and inv.description:
                result.append((inv.id, "%s - %s" % (inv.cost_center or '', inv.description or '')))
            elif inv.status_code:
                result.append((inv.id, "%s" % (inv.cost_center or '')))
            elif inv.description:
                result.append((inv.id, "%s" % (inv.description or '')))
        return result
    
nstda_mst_cost_center()

####################################################################################################

class nstda_mst_location(models.Model):
    
    _name = 'nstda.mst.location'
    _rec_name = 'description'
     
    plant = fields.Char('Plant')  
    location_code = fields.Char('Location Code',size=20)  
    description = fields.Char('Description',size=50)   
    
    _order = 'plant ASC'
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.location_code and inv.description:
                result.append((inv.id, "%s - %s" % (inv.location_code or '', inv.description or '')))
            elif inv.location_code:
                result.append((inv.id, "%s" % (inv.location_code or '')))
            elif inv.description:
                result.append((inv.id, "%s" % (inv.description or '')))
        return result


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search(['|', ('location_code', 'ilike', name), ('description', 'ilike', name), ] + args, limit=limit)
        if not recs:
            recs = self.search(['|', ('location_code', operator, name), ('description', operator, name), ] + args, limit=limit)
        return recs.name_get()
 
nstda_mst_location()

####################################################################################################

class nstda_mst_employee(models.Model):
    
    _name = 'nstda.mst.employee'
    _rec_name = 'name'
    
    personnel_number = fields.Char('Personnel Number',size=6)  
    name = fields.Char('Name')
    business_area = fields.Char('Business Area') 
    cost_center = fields.Char('Cost Center')  
    position = fields.Char('Position')  
    
#      _order = 'name_relet_group ASC'

####################################################################################################

class nstda_mst_internal_order(models.Model):
    
    _name = 'nstda.mst.internal.order'
    _rec_name = 'io_code'
    
    io_code = fields.Char('IO Code',size=8)  
    description = fields.Char('Description',size=50)
    
#      _order = 'unit_in_nstda ASC'

####################################################################################################

class nstda_mst_wbs(models.Model):
    
    _name = 'nstda.mst.wbs'
    _rec_name = 'wbs_code'
    
    wbs_code = fields.Char('WBS Code',size=12)  
    description = fields.Char('Description',size=50)
    
#      _order = 'unit_in_nstda ASC'

####################################################################################################

class  nstda_mst_asset_status(models.Model):
    
    _name = 'nstda.mst.asset.status'
    _rec_name = 'description'

    status_code = fields.Char('Status Code',size=4)  
    description = fields.Char('Description',size=50)
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.status_code and inv.description:
                result.append((inv.id, "%s - %s" % (inv.status_code or '', inv.description or '')))
            elif inv.status_code:
                result.append((inv.id, "%s" % (inv.status_code or '')))
            elif inv.description:
                result.append((inv.id, "%s" % (inv.description or '')))
        return result
    
nstda_mst_asset_status()

####################################################################################################
 
class nstda_mst_purchasing_method(models.Model):

    _name = 'nstda.mst.purchasing.method'
    _rec_name = 'description'
    
    purmenthod_code = fields.Char('PurMenthod Code',size=3)
    description = fields.Char('Description',size=50)
    
    @api.multi
    def name_get(self):
        result = []
        for inv in self:
            if inv.purmenthod_code and inv.description:
                result.append((inv.id, "%s - %s" % (inv.purmenthod_code or '', inv.description or '')))
            elif inv.status_code:
                result.append((inv.id, "%s" % (inv.purmenthod_code or '')))
            elif inv.description:
                result.append((inv.id, "%s" % (inv.description or '')))
        return result
    
nstda_mst_purchasing_method()

####################################################################################################

class nstda_mst_vendor(models.Model):

    _name = 'nstda.mst.vendor'
    _rec_name = 'vender_code'
    
    vender_code = fields.Char('Vender  Code',size=8)
    name = fields.Char('Name',size=50)
    address = fields.Char('Address',size=50)

####################################################################################################
 
class nstda_mst_asset_class(models.Model):

    _name = 'nstda.mst.asset.class'
    _rec_name = 'class_name'
    
    class_code = fields.Char('Code  Code',size=8)
    class_name = fields.Char('Name',size=50)

####################################################################################################
