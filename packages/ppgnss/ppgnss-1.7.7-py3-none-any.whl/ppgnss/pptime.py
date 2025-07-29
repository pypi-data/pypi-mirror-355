import argparse
import sys
from ppgnss import gnss_time

# 自定义解析函数
def parse_year_doy(value):
    year, doy = map(int, value.split(','))
    return year, doy

def parse_ymd(value):
    year, month, day = map(int, value.split(','))
    return year, month, day

def parse_gpsw(value):
    gpsw, dow = map(int, value.split(','))
    return gpsw, dow

def parse_arguments():
    parser = argparse.ArgumentParser(description="Process GNSS time related parameters")
    
    # 添加所有可能的命令行参数
    parser.add_argument('--doy', type=parse_year_doy, help="Year and Day of Year (format: year,doy)")
    parser.add_argument('--ymd', type=parse_ymd, help="Year, Month and Day (format: year,month,day)")
    parser.add_argument('--gpsw', type=parse_gpsw, help="GPS Week and Day of Week (format: gpsw,dow)")
    parser.add_argument('--jd', type=float, help="Julian Date")
    parser.add_argument('--mjd', type=float, help="Modified Julian Date")

    args = parser.parse_args()

    # 参数验证
    if args.jd is not None:
        # 情况(4)：只包含 --jd 参数
        if any([args.doy, args.gpsw, args.mjd, args.ymd]):
            raise ValueError("Error: --jd cannot be used with other parameters.")
    elif args.mjd is not None:
        # 情况(5)：只包含 --mjd 参数
        if any([args.doy, args.gpsw, args.jd, args.ymd]):
            raise ValueError("Error: --mjd cannot be used with other parameters.")
    elif args.doy is not None:
        # 情况(1)：只包含 --doy 参数
        year, doy = args.doy
        pass  # 这是有效的，不需要额外处理
    elif args.gpsw is not None:
        # 情况(2)：只包含 --gpsw 参数
        pass  # 这是有效的，不需要额外处理
    elif args.ymd is not None:
        # 情况(3)：只包含 --ymd 参数
        year, month, day = args.ymd
        pass  # 这是有效的，不需要额外处理
    else:
        # 如果没有输入参数，则显示用法
        parser.print_help()
        sys.exit(1)

    return args

def convert_and_output(args):
    # 输出结果的统一顺序：JD, GPS Week/DOW, YMD, DOY, MJD
    jd = gpsw = dow = year = month = day = doy = mjd = None
    
    if args.jd is not None:
        # 转换 Julian Date
        jd = args.jd
        gpsw, dow = gnss_time.jd2gpsw(jd)
        year, month, day = gnss_time.jd2ymd(jd)
        year, doy = gnss_time.jd2doy(jd)
        mjd = gnss_time.jd2mjd(jd)
    elif args.mjd is not None:
        # 转换 MJD
        mjd = args.mjd
        jd = gnss_time.mjd2jd(mjd)
        gpsw, dow = gnss_time.jd2gpsw(jd)
        year, month, day = gnss_time.jd2ymd(jd)
        year, doy = gnss_time.jd2doy(jd)
    elif args.doy is not None:
        # 转换 DOY
        year, doy = args.doy
        jd = gnss_time.doy2jd(year, doy)
        gpsw, dow = gnss_time.jd2gpsw(jd)
        year, month, day = gnss_time.jd2ymd(jd)
        mjd = gnss_time.jd2mjd(jd)
    elif args.gpsw is not None:
        # 转换 GPS Week
        gpsw, dow = args.gpsw
        jd = gnss_time.gpsw2jd(gpsw, dow)
        year, month, day = gnss_time.jd2ymd(jd)
        year, doy = gnss_time.jd2doy(jd)
        mjd = gnss_time.jd2mjd(jd)
    elif args.ymd is not None:
        # 转换 YMD
        year, month, day = args.ymd
        jd = gnss_time.ymd2jd(year, month, day)
        gpsw, dow = gnss_time.jd2gpsw(jd)
        year, doy = gnss_time.jd2doy(jd)
        mjd = gnss_time.jd2mjd(jd)

    # 输出结果：确保dow, day, doy都是整数
    print(f"JD       : {jd}")
    print(f"GPS Week : {gpsw}, {int(dow)}")  # dow转为整数
    print(f"YMD      : {year}, {month:02d}, {int(day):02d}")  # day转为整数
    print(f"DOY      : {year}, {int(doy):03d}")  # doy转为整数
    print(f"MJD      : {mjd}")


def main():
    try:
        args = parse_arguments()
        convert_and_output(args)
    except ValueError as e:
        print(f"Argument error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()