#!/usr/bin/env python
# coding: utf-8

# In[10]:


# %%capture
# !pip install fiona

# %%capture
# !pip install geopandas


# In[11]:


import pandas as pd
import geopandas as gdp
import math
import json

from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import widgetbox, row, column


# Đầu tiên ta đọc dữ liệu thường vào DataFrame. Đổi tên cột cho dễ thao tác

# In[12]:


df = pd.read_csv('https://raw.githubusercontent.com/teddyorkie/python_datascience/master/data/E11.14.csv', 
                 skiprows=1, na_values="..")
df = df.rename(columns={"Cities, Provinces":"Province", "Non public":"Private"})
df.sample(5)


# Đọc dữ liệu geojson vào một geopandas dataframe. Đổi tên cột, và vứt bớt những thứ không cần thiết. Lưu ý, tên cột muốn join với dữ liệu thường phải trùng với tên cột bên trên.

# In[13]:


vn_df = gdp.read_file('https://raw.githubusercontent.com/teddyorkie/python_datascience/master/data/VN_provinces.geojson')
vn_df = vn_df.rename(columns={'NAME_1':'Name', 'VARNAME_1':'Province'}).set_geometry('geometry')
col_to_drop = list(range(4)) + list(range(6,11))
vn_df.drop(vn_df.columns[col_to_drop], axis=1, inplace=True)
vn_df.sample(3)


# Dataframe format này cho phép ta thay đổi range màu, cũng như format các loại dữ liệu khác nhau khi người dùng gọi hàm call-back trên interactive bohker server.

# In[14]:


# This dictionary contains the formatting for the data in the plots
# Outliers are Ha Noi & Ho Chi Minh, so we cap at 4K so that other province
# can have some color.
format_data = [('Total', 0, 4000, '0,0', 'Tổng số bác sĩ') ]
 
#Create a DataFrame object from the dictionary 
format_df = pd.DataFrame(format_data, columns = ['field' , 'min_range', 'max_range' , 'format', 'verbage'])
format_df.head(10)


# In[15]:


# Hàm này merge dữ liệu và chuyển sang format json
def json_data():
  merged = pd.merge(vn_df, df, on="Province", how='left')
  merged_json = json.loads(merged.to_json())
  json_data = json.dumps(merged_json)
  return json_data

def make_plot(field_name):
  # Set the format of the colorbar
  min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
  max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
  field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]  

  # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
  color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)

  # Create color bar.
  format_tick = NumeralTickFormatter(format=field_format)
  color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, 
                       formatter=format_tick, border_line_color=None, location = (0, 0))

  # Create figure object.
  verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

  p = figure(title = verbage + ' thống kê theo tỉnh thành VN - 2018', toolbar_location=None, plot_width = 450)
  p.xgrid.grid_line_color = None
  p.ygrid.grid_line_color = None
  p.axis.visible = False

  p.patches('xs','ys', source = geosource, fill_color = {'field' : field_name, 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)
  
  # Specify color bar layout
  p.add_layout(color_bar, 'right')
  return p

# Define the callback function: update_plot
def update_plot(attr, old, new):
    # The input yr is the year selected from the slider
    yr = slider.value
    new_data = json_data(yr)
    
    # The input cr is the criteria selected from the select box
    cr = select.value
    input_field = format_df.loc[format_df['verbage'] == cr, 'field'].iloc[0]
    
    # Update the plot based on the changed inputs
    p = make_plot(input_field)
    
    # Update the layout, clear the old document and display the new document
    layout = column(p, widgetbox(select), widgetbox(slider))
    curdoc().clear()
    curdoc().add_root(layout)
    
    # Update the data
    geosource.geojson = new_data


# In[16]:


# Chuẩn bị dữ liệu GeoJSONDataSource
geosource = GeoJSONDataSource(geojson = json_data())


# In[17]:


# Define a sequential multi-hue color palette.
# Reverse color order so that dark blue is highest obesity.
palette = brewer['Blues'][8]
palette = palette[::-1]

# Tên cột không được để tiếng Việt có dấu, hiện không được support hiển thị
hover = HoverTool(tooltips = [ ('Tỉnh', '@Name'),
                               ('Tổng số bác sĩ', '@Total'),
                               ('Công lập', '@Public'),
                               ('Tư', '@Private') ])    

p = make_plot('Total') 
p.add_tools(hover)         

# Make a slider object: slider 
# slider = Slider(title = 'Year',start = 2012, end = 2018, step = 1, value = 2018)
# slider.on_change('value', update_plot)

# # Make a selection object: select
# select = Select(title='Select Criteria:', value='Tổng số bác sĩ', 
#                 options=['Tổng số bác sĩ', 'Tổng số giáo viên trực tiếp'])
# select.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p) # , widgetbox(select), widgetbox(slider))
curdoc().add_root(layout)

# Use the following code to test in a notebook
# Interactive features will no show in notebook
# output_notebook()
# show(p)

