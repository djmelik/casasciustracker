#!/usr/bin/env python

import datetime
from flask import Flask, render_template
from flask_admin import Admin, BaseView, expose
from flask_mongoengine import MongoEngine
from flask_admin.contrib.mongoengine import ModelView, filters
from flask_admin.contrib.mongoengine.filters import FilterEqual, FilterInList, FilterNotEqual, FilterNotInList
from decimal import Decimal, getcontext
from jinja2 import Markup
from collections import Counter

# Create app
app = Flask(__name__, template_folder='templates')
app.debug = False
app.config['FLASK_ADMIN_FLUID_LAYOUT']=True
app.config['MONGODB_SETTINGS'] = {'DB': 'tracker'}

# Create database models
db = MongoEngine()
db.init_app(app)

class Coin(db.Document):
  index = db.IntField()
  address = db.StringField()
  txcount = db.IntField()
  incount = db.IntField()
  outcount = db.IntField()
  balance = db.DecimalField(precision=8)
  type = db.StringField()
  series = db.StringField()
  status = db.StringField()
  value = db.DecimalField(precision=8)
  create_txid = db.StringField()
  create_block = db.StringField()
  create_time = db.IntField()
  redeem_txid = db.StringField()
  redeem_block = db.StringField()
  redeem_time = db.IntField()
  update_time = db.IntField()

  def __unicode__(self):
    return self.name

def get_all_types():
  return (
    ('S1-COIN-1',      'Series 1 - 1 BTC (Error)'),
    ('S1-COIN-5',      'Series 1 - 5 BTC'),
    ('S1-COIN-25',     'Series 1 - 25 BTC'),
    ('S1-COIN-1000',   'Series 1 - 1000 BTC (Coin)'),
    ('S1-BAR-100',     'Series 1 - 100 BTC (Bar)'),
    ('S1-BAR-500',     'Series 1 - 500 BTC (Bar)'),
    ('S1-BAR-1000',    'Series 1 - 1000 BTC (Bar)'),
    ('S2-COIN-0.5',    'Series 2 - 0.5 BTC'),
    ('S2-COIN-1-2011', 'Series 2 - 1 BTC (2011)'),
    ('S2-COIN-1-2012', 'Series 2 - 1 BTC (2012)'),
    ('S2-COIN-1-2013', 'Series 2 - 1 BTC (2013)'),
    ('S2-COIN-5',      'Series 2 - 5 BTC'),
    ('S2-COIN-10',     'Series 2 - 10 BTC'),
    ('S2-COIN-25',     'Series 2 - 25 BTC'),
    ('S2-BAR-100',     'Series 2 - 100 BTC (Bar)'),
    ('S2-BAR-500',     'Series 2 - 500 BTC (Bar)'),
    ('S2-BAR-DIY',     'Series 2 - DIY Storage (Bar)'),
    ('S3-COIN-0.1-AG', 'Series 3 - 0.1 BTC Silver'),
    ('S3-COIN-0.5-AG', 'Series 3 - 0.5 BTC Silver'),
    ('S3-COIN-1-AG',   'Series 3 - 1.0 BTC Silver'),
  )
  
class CasasciusView(ModelView):

  def __init__(self, model, session, *args, **kwargs):
    super(CasasciusView, self).__init__(model, session, *args, **kwargs)
    self.static_folder = 'static'
    self.endpoint = 'admin'
    self.name = 'Tracker'

  def get_all_status():
    return (
      ('Active',   'Active'),
      ('Redeemed', 'Redeemed'),
      ('Unused',   'Unused'),
    )

  def get_all_series():
    return (
      ('1', 'Series 1'),
      ('2', 'Series 2'),
      ('3', 'Series 3'),
    )

  def _balance(view, context, model, name):
    getcontext().prec = 8
    balance = Decimal(model.balance).normalize()
    return '{0:f}'.format(balance)
        
  def _create_time(view, context, model, name):
    if model.create_time is not None:
      label = "label-success"
      create_time_human = datetime.datetime.fromtimestamp(int(model.create_time)).strftime('%Y-%m-%d %H:%M:%S')
      markupstring = "<span class='label %s'>%s</span>" % (label, create_time_human)
      return Markup(markupstring)
    return model.create_time
        
  def _redeem_time(view, context, model, name):
    if model.redeem_time is not None:
      label = "label-danger"
      redeem_time_human = datetime.datetime.fromtimestamp(int(model.redeem_time)).strftime('%Y-%m-%d %H:%M:%S')
      markupstring = "<span class='label %s'>%s</span>" % (label, redeem_time_human)
      return Markup(markupstring)
    return model.redeem_time

  def _update_time(view, context, model, name):
    if model.update_time is not None:
      label = "label-default"
      update_time_human = datetime.datetime.fromtimestamp(int(model.update_time)).strftime('%Y-%m-%d %H:%M:%S')
      markupstring = "<span class='label %s'>%s</span>" % (label, update_time_human)
      return Markup(markupstring)
    return model.update_time
        
  def _address(view, context, model, name):
    markupstring = "<a href='https://www.smartbit.com.au/address/%s'>%s</a>" % (model.address, model.address)
    return Markup(markupstring)
        
  def _create_txid(view, context, model, name):
    markupstring = "<a href='https://www.smartbit.com.au/tx/%s'>%s</a>" % (model.create_txid, model.create_txid)
    return Markup(markupstring)
        
  def _redeem_txid(view, context, model, name):
    markupstring = "<a href='https://www.smartbit.com.au/tx/%s'>%s</a>" % (model.redeem_txid, model.redeem_txid)
    return Markup(markupstring)
        
  def _type(view, context, model, name):
    if model.type is not None:
      label = "label-primary"
      markupstring = "<span class='label %s'>%s</span>" % (label, model.type)
      return Markup(markupstring)
    return model.type
        
  def _create_block(view, context, model, name):
    if model.create_block is not None:
      markupstring = "<a href='https://www.smartbit.com.au/block/%s'>%s</a>" % (model.create_block, model.create_block)
      return Markup(markupstring)
    return model.create_block
        
  def _redeem_block(view, context, model, name):
    if model.redeem_block is not None:
      markupstring = "<a href='https://www.smartbit.com.au/block/%s'>%s</a>" % (model.redeem_block, model.redeem_block)
      return Markup(markupstring)
    return model.redeem_block
        
  def _value(view, context, model, name):
    if model.value is not None:
      getcontext().prec = 8
      value = Decimal(model.value).normalize()
      return '{0:f}'.format(value)
    return model.value
        
  def _status(view, context, model, name):
    label = ''
    if model.status == "Active":
      label = "label-success"
    elif model.status == "Redeemed": 
      label = "label-danger"
    else:
      label = "label-warning"
    markupstring = "<span class='label %s'>%s</span>" % (label, model.status)
    return Markup(markupstring)
 
  # Model page
  list_template = 'list.html' # Set template file.

  can_create = False          # Disable creation of records.
  can_edit = False            # Disable editing of records.
  can_delete = False          # Disable deletion of records.

  can_set_page_size = True    # Allow user to set row size.
  page_size = 20             # Default row size.

  can_view_details = True     # Allow user to view details.
  can_export = True           # Allow user to export data (CSV files).
  named_filter_urls = True    # Display URLs using field names.


  # Column fields
  column_list = [ 
    'index',
    'address',
    'series',
    'type',
    'status',
    'value',
    'balance',
    'create_block',
    'redeem_block',
    'create_time',
    'redeem_time',
    'update_time',
  ]

  # Column field formatters for displaying
  column_formatters = {
    'balance': _balance,
    'value': _value,
    'status': _status,
    'address': _address,
    'type': _type,
    'create_time': _create_time,
    'redeem_time': _redeem_time,
    'update_time': _update_time,
    'create_txid': _create_txid,
    'create_block': _create_block,
    'redeem_txid': _redeem_txid,
    'redeem_block': _redeem_block,
  }

  # Column field formatters for exporting 
  column_formatters_export = {}

  # Searchable fields
  column_searchable_list = [
    'address',
    'type',
    'series',
    'create_txid',
    'redeem_txid',
    'status',
    'create_block',
    'redeem_block',
  ]

  # Column filters
  column_filters = [
    'index',
    'address',
    'balance',
    'txcount',
    'incount',
    'outcount',

    FilterEqual(column=Coin.type, name='Type', options=get_all_types()),
    FilterNotEqual(column=Coin.type, name='Type', options=get_all_types()),
    FilterInList(column=Coin.type, name='Type', options=get_all_types()),
    FilterNotInList(column=Coin.type, name='Type', options=get_all_types()),
    
    FilterEqual(column=Coin.series, name='Series', options=get_all_series()),
    FilterNotEqual(column=Coin.series, name='Series', options=get_all_series()),
    FilterInList(column=Coin.series, name='Series', options=get_all_series()),
    FilterNotInList(column=Coin.series, name='Series', options=get_all_series()),
    
    FilterEqual(column=Coin.status, name='Status', options=get_all_status()),
    FilterNotEqual(column=Coin.status, name='Status', options=get_all_status()),
    FilterInList(column=Coin.status, name='Status', options=get_all_status()),
    FilterNotInList(column=Coin.status, name='Status', options=get_all_status()),

    'value',
    'create_txid',
    'create_block',
    'create_time',
    'redeem_txid',
    'redeem_block',
    'redeem_time',
  ]

class CasasciusChartsStatus(BaseView):
  @expose('/')
  def index(self): 
    labels = map(lambda x: x[1], get_all_types())
    active_values = map(lambda x: Coin.objects(type=x[0], status='Active').count(), get_all_types())
    redeem_values = map(lambda x: Coin.objects(type=x[0], status='Redeemed').count(), get_all_types())
    return self.render('status.html', labels=labels, active_values=active_values, redeem_values=redeem_values)

class CasasciusChartsCreation(BaseView):
  @expose('/')
  def index(self): 
    total_coins = 0
    total_active = [] 

    create_coins = sorted(Counter(map(lambda x: datetime.datetime.fromtimestamp(x['create_time']).strftime('%y-%m-01'), Coin.objects(status__in=['Redeemed', 'Active'], type__ne='S2-BAR-DIY'))).items())
    create_date = map(lambda x: x[0], create_coins)
    create_count = map(lambda x: x[1], create_coins)

    for i in create_count:
      total_coins = total_coins + i
      total_active.append(total_coins)

    return self.render('creation.html', create_date=create_date, create_count=create_count, total_active=total_active)

class CasasciusChartsRedeemed(BaseView):
  @expose('/')
  def index(self): 
    total_coins = Coin.objects(status__in=['Active', 'Redeemed'], type__ne='S2-BAR-DIY').count()
    total_redeem_coins = 0
    total_active = [] 
    total_redeem = []

    redeem_coins = sorted(Counter(map(lambda x: datetime.datetime.fromtimestamp(x['redeem_time']).strftime('%y-%m-01'), Coin.objects(status='Redeemed', type__ne='S2-BAR-DIY', redeem_time__ne=None))).items())
    redeem_date = map(lambda x: x[0], redeem_coins)
    redeem_count = map(lambda x: x[1], redeem_coins)

    for i in redeem_count:
      total_coins = total_coins - i
      total_redeem_coins = total_redeem_coins + i

      total_redeem.append(total_coins)
      total_active.append(total_redeem_coins)

    return self.render('redeemed.html', redeem_date=redeem_date, redeem_count=redeem_count, total_redeem=total_redeem, total_active=total_active)

class CasasciusChartsValue(BaseView):
  @expose('/')
  def index(self): 
    total_coins = Coin.objects(status__in=['Active', 'Redeemed'], type__ne='S2-BAR-DIY')
    total_redeem_coins = Coin.objects(status__in=['Redeemed'], type__ne='S2-BAR-DIY', redeem_time__ne=None)
    # Temp hack: Fix
    total_coin_value = Decimal(91264.50000000)
    total_redeem_value = 0
    total_active = [] 
    total_redeem = []

    redeem_coins = sorted(Counter(map(lambda x: datetime.datetime.fromtimestamp(x['redeem_time']).strftime('%y-%m-01'), Coin.objects(status='Redeemed', type__ne='S2-BAR-DIY', redeem_time__ne=None))))
    redeem_table = dict.fromkeys(redeem_coins, 0)

    for coin in total_redeem_coins:
      redeem_date = datetime.datetime.fromtimestamp(coin['redeem_time']).strftime('%y-%m-01')
      redeem_table[redeem_date] += coin['value']
    
    redeem_date = map(lambda x: x[0], sorted(list(redeem_table.items())))
    redeem_count = map(lambda x: x[1], sorted(list(redeem_table.items())))

    for value in redeem_count:
      total_coin_value = total_coin_value - value
      total_redeem_value = total_redeem_value + value

      total_active.append(total_coin_value)
      total_redeem.append(total_redeem_value)

    return self.render('redeemed_value.html', redeem_date=redeem_date, redeem_count=redeem_count, total_redeem=total_redeem, total_active=total_active)


# Main

if __name__ == '__main__':

  # Create FlaskAdmin App
  admin = Admin(
    app,
    name='Casascius Tracker',
    template_mode='bootstrap3',
    index_view=CasasciusView(Coin, db, url='/')
  )
	
  # Add Views
  admin.add_view(CasasciusChartsStatus(name='Status', endpoint='status', category='Analytics'))
  admin.add_view(CasasciusChartsCreation(name='Creation', endpoint='creation', category='Analytics'))
  admin.add_view(CasasciusChartsRedeemed(name='Redeemed', endpoint='redeemed', category='Analytics'))
  admin.add_view(CasasciusChartsValue(name='Value', endpoint='value', category='Analytics'))
	
  # Start Application
  app.run(host='0.0.0.0')
