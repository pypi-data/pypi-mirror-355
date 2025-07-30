from datetime import datetime as dt

def get_time(launch_datetime_str):

    if 'T' in launch_datetime_str:
        launch = dt.strptime(rf'{launch_datetime_str}','%Y-%m-%dT%H:%M:%SZ')
    else:
        launch = dt.strptime(rf'{launch_datetime_str}','%Y-%m-%d %H:%M:%S')

    date = launch.strftime('%d/%m/%Y')
    hour = launch.strftime('%H:%M')
    res_seconds = (launch - dt.utcnow()).total_seconds()
    return {'hour':hour,'date':date,'res_seconds':res_seconds}
    
