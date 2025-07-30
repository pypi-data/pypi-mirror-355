
from tpf.tim import current_time 

t = current_time()

print(t)  # 2022-07-08 17:38:21


import time 

t_str = time.strptime("2022-07-08 17:38:21",'%Y-%m-%d %H:%M:%S')
print(t_str)  # time.struct_time(tm_year=2022, tm_mon=7, tm_mday=8, tm_hour=17, tm_min=38, tm_sec=21, tm_wday=4, tm_yday=189, tm_isdst=-1)

# 转化为时间戳
print(time.mktime(t_str))  # 1657273101.0

from datetime import datetime 
dt = datetime.now()  
print(dt.strftime('%Y-%m-%d %H:%M:%S'))  # 2022-07-08 17:45:28
print(dt.strptime("2022-07-08 17:45:28",'%Y-%m-%d %H:%M:%S')) # 2022-07-08 17:45:28

print('今天是这周的第%s天 '  % dt.strftime( '%w' )  )  # 今天是这周的第5天 
print('今天是今年的第%s天 '  % dt.strftime( '%j' ) )  # 今天是今年的第189天
print('今周是今年的第%s周 '  % dt.strftime( '%U' )  ) # 今周是今年的第27周 



from datetime import datetime 

def parse_ymd(ss):
    year_str,mon_str,day_str = ss.split('-')
    return datetime(int(year_str),int(mon_str),int(day_str))

print(parse_ymd("2025-12-25"))  # 2025-12-25 00:00:00