import requests
import sqlite3
import re

# Database file
DB_FILE = "data/gaokao.db"

data=[{'text': '北京', 'selected': '0', 'options': [{'text': '2024本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2024专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2023本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2022本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2021本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2020本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '天津', 'selected': '0', 'options': [{'text': '2024本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2024专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2023本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2022本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2021本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2020本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '河北', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '山西', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '内蒙古', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '辽宁', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '吉林', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '黑龙江', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '上海', 'selected': '0', 'options': [{'text': '2024本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2024专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2023本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2022本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2021本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2020本科', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020专科', 'selected': '0', 'options': [{'text': '语数外', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}]}, {'text': '江苏', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '浙江', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}]}, {'text': '安徽', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '福建', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '江西', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023本科', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022本科', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021本科', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020本科', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '山东', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '河南', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '湖北', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '湖南', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '广东', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '广西', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '海南', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '3+3综合', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '重庆', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '四川', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '贵州', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '云南', 'selected': '1', 'options': [{'text': '2024', 'selected': '1', 'options': [{'text': '理科', 'selected': '1'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '西藏(暂无数据)', 'selected': '0', 'options': [], 'disabled': True}, {'text': '陕西', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '甘肃', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '物理类', 'selected': '0'}, {'text': '历史类', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '青海', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '宁夏', 'selected': '0', 'options': [{'text': '2024', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2023', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2022', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2021', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2020', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2019', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}, {'text': '2018', 'selected': '0', 'options': [{'text': '理科', 'selected': '0'}, {'text': '文科', 'selected': '0'}]}]}, {'text': '新疆(暂无数据)', 'selected': '0', 'options': [], 'disabled': True}]

def init_db(conn):
    cursor = conn.cursor()

    # Create t_exam_contexts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS t_exam_contexts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        province TEXT NOT NULL,
        year TEXT NOT NULL,
        category TEXT NOT NULL,
        created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
        updated_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
        UNIQUE (province, year, category)
    )
    """)

    # Create t_score_segments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS t_score_segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        context_id INTEGER NOT NULL,
        max_order INTEGER,
        max_score INTEGER,
        min_order INTEGER,
        min_score INTEGER,
        student_count INTEGER,
        created_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
        updated_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'))
    )
    """)

    conn.commit()

def fetch_segment(prov, year_param, category):
    params = {
        "fromCard": 1,
        "resource_id": 50266,
        "province": prov,
        "year": year_param, # API uses the string like "2024" or "2024本科"
        "category": category,
        "query": "一分一段",
    }

    try:
        # It's good practice to handle potential SSL issues, but verify=False is kept as per original
        # For production, consider providing a CA bundle or setting up certs properly.
        # requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        res = requests.get(
            "https://opendata.baidu.com/api.php",
            params=params,
            verify=False, 
            timeout=10,
        ).json()
        
        # Check for empty or error result from API
        if not res or not res.get("Result") or not res["Result"][0].get("DisplayData"): 
            print(f"{prov} {year_param} {category} - API returned no or malformed DisplayData.")
            return None
            
        seg_info = res["Result"][0]["DisplayData"]["resultData"]["tplData"][
            "segmentInfo"
        ]
        if not seg_info: # Handle cases where segmentInfo might be empty
            print(f"{prov} {year_param} {category} - No segmentInfo found in API response.")
            return None
            
        seg_list = []
        for i in seg_info:
            # Ensure segment exists and is valid before splitting
            if not i.get("segment") or '-' not in i["segment"]:
                print(f"{prov} {year_param} {category} - Invalid segment format: {i.get('segment')}")
                continue
            seg = list(map(int, i["segment"].split("-")))
            seg_list.append({"max": seg[0], "min": seg[1], "info": i.get("segList", [])})
        
        if not seg_list: # If all segments were invalid or empty
             print(f"{prov} {year_param} {category} - No valid segments processed.")
             return None

        return {
            "province": prov,
            "year_param": year_param, # The original year string used for API call
            "category": category,
            "seglist": seg_list,
        }
    except requests.exceptions.RequestException as e:
        print(f"{prov} {year_param} {category} 数据请求失败 (Network/Request error): {e}")
        return None
    except (KeyError, IndexError, TypeError, ValueError) as e:
        print(f"{prov} {year_param} {category} 数据解析失败 (Data structure error): {e}")
        # print(f"Problematic API response snippet: {str(res)[:500]}") # For debugging
        return None
    except Exception as e: # Catch any other unexpected errors
        print(f"{prov} {year_param} {category} 数据请求或解析时发生未知错误: {e}")
        return None

def parse_year_from_string(year_str):
    match = re.search(r'\d{4}', year_str)
    if match:
        return int(match.group(0))
    return None # Or raise an error, or return a default

def save_data_to_sqlite(cursor, result_data):
    """Saves fetched segment data to SQLite database."""
    segments_inserted_count = 0
    prov = result_data["province"]
    year = result_data["year_param"]
    category = result_data["category"]
    try:
        # Get or insert exam context
        cursor.execute("""
        INSERT OR IGNORE INTO t_exam_contexts (province, year, category)
        VALUES (?, ?, ?)
        """, (prov, year, category))
        
        cursor.execute("""
        SELECT id FROM t_exam_contexts
        WHERE province = ? AND year = ? AND category = ?
        """, (prov, year, category))
        context_id_row = cursor.fetchone()
        if not context_id_row:
            print(f"    ERROR: Could not get context_id for {prov} {year} {category}")
            return 0
        context_id = context_id_row[0]

        # Insert score segments
        for segment_group in result_data["seglist"]:
            for score_detail in segment_group["info"]:
                max_order = score_detail["maxOrder"]
                max_score = score_detail["maxScore"]
                min_order = score_detail["minOrder"]
                min_score = score_detail["minScore"]
                student_count = score_detail["num"]

                if max_order == '-' or min_order == '-': # 针对边界情况的特殊处理
                    continue

                cursor.execute("""
                INSERT INTO t_score_segments
                (context_id, max_order, max_score, min_order, min_score, student_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (context_id, max_order, max_score, min_order, min_score, student_count))
                segments_inserted_count += 1
        
        if segments_inserted_count > 0:
            print(f"    Successfully inserted {segments_inserted_count} score segments for {prov} - {year} - {category}.")
        else:
            print(f"    No score segments found or inserted for {prov} - {year} - {category}.")
        return segments_inserted_count
                            
    except sqlite3.Error as e:
        print(f"    SQLite error while processing {prov} {year} {category}: {e}")
        # conn.rollback() # Rollback should be handled by the caller (main function)
        raise # Re-raise the exception to be caught by the main loop for rollback
    except Exception as e:
        print(f"    Unexpected error while processing {prov} {year} {category} into DB: {e}")
        raise # Re-raise for the same reason

def main():
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)
    cursor = conn.cursor()

    total_records_processed = 0

    for prov_data in data:
        prov_name = prov_data["text"]
        print(f"Processing province: {prov_name}")
        province_score_segments_count = 0

        for contextInfo in prov_data.get("options", []):
            year_param_for_api = contextInfo["text"] # e.g., "2024本科" or "2019"

            for categoryInfo in contextInfo.get("options", []):
                category_name = categoryInfo["text"]
                
                print(f"  Fetching data for {prov_name} - {year_param_for_api} - {category_name}...")
                result = fetch_segment(prov_name, year_param_for_api, category_name)

                if result:
                    try:
                        # Pass year_param_for_api (the full string) as year_for_db
                        inserted_count = save_data_to_sqlite(cursor, result)
                        province_score_segments_count += inserted_count
                    except (sqlite3.Error, Exception) as e: # Catch errors from save_data_to_sqlite
                        print(f"  An error occurred during DB operation for {prov_name} - {year_param_for_api} - {category_name}. Rolling back this context.")
                        conn.rollback() # Rollback on error for this specific context
                else:
                    print(f"  No data fetched for {prov_name} - {year_param_for_api} - {category_name}.")
        
        if province_score_segments_count > 0:
            conn.commit() # Commit per province
            print(f"Province {prov_name}: Committed {province_score_segments_count} score segments to database.")
            total_records_processed += province_score_segments_count
        else:
            print(f"Province {prov_name}: No new score segments to commit.")

    conn.close()
    print(f"Finished processing. Total score segments saved to database: {total_records_processed}")

if __name__ == "__main__":
    main()