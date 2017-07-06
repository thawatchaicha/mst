# -*- coding: utf-8 -*-
{
        "name" : "NSTDA-APP :: myAsset",
        "version" : "2.0",
        "author" : 'Thawatchai C.',
        "category" : 'NSTDA Apps',
        "description": """ myAsset ระบบครุภัณฑ์ """,
        'website': 'http://www.nstda.or.th',
        'depends': [
                    'mail', 'nstdaconf_blockfile', 'base', 'nstdamas',
                    ],
        'data': [
                'security/module_data.xml',
                'security/nstda_mst_security.xml',
                'security/ir.model.access.csv', 
                
                'data/nstda.mst.location.csv',
                'data/nstda.mst.asset.status.csv',
                'data/nstda.mst.purchasing.method.csv',
                
                'static/src/views/nstda_mst.xml',
                
                'views/nstda_mst_view.xml',
                'views/nstda_mst_sequence.xml',
                'views/nstda_mst_cost_center_view.xml',
                'views/nstda_mst_transfer_view.xml',
                'views/nstda_mst_menu_view.xml',
                
        ],
        'demo': [],
        'installable': True,
        'images': [],
}
