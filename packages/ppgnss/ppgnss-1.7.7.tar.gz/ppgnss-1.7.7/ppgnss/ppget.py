#!/usr/bin/python3

import argparse
import wget
from datetime import datetime, timedelta
from ppgnss import gnss_time  # 导入 ppnss 库中的时间转换模块
import os


def parse_year_and_doy(value):
    try:
        year, doy = map(int, value.split(','))
        return year, doy
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid year,doy format. Example: --from 2023,100")


def download_brdc_data(year, doy, out_dir="."):
    base_url = "ftp://igs.gnsswhu.cn/pub/gps/data/daily"
    yr = str(year)[2:]
    doy_str = f"{doy:03d}"  # 使用 zfill 将 doy 格式化为三位数字
    url = f"{base_url}/{year}/{doy_str}/{yr}p/BRDM00DLR_S_{year}{doy_str}0000_01D_MN.rnx.gz"
    filename = os.path.join(out_dir, f"BRDM00DLR_S_{year}{doy_str}0000_01D_MN.rnx.gz")

    try:
        wget.download(url, out=filename)
        print(f"\nDownloaded BRDC data for {year}-{doy_str} to {filename}")
    except Exception as e:
        print(f"Failed to download BRDC data for {year}-{doy_str}. Error: {e}")


def download_gim_data(year, doy, out_dir="."):
    base_url = "http://ftp.aiub.unibe.ch/CODE"
    yr = str(year)[2:]
    doy_str = f"{doy:03d}"  # 使用 zfill 将 doy 格式化为三位数字

    # 判断时间，选择不同的 URL
    if datetime(year, 1, 1) + timedelta(days=doy - 1) <= datetime(2022, 11, 26):  # 2022年330天或之前
        url = f"{base_url}/{year}/CODG{doy_str}0.{yr}I.Z"
    else:
        url = f"{base_url}/{year}/COD0OPSFIN_{year}{doy_str}0000_01D_01H_GIM.INX.gz"

    # 本地文件名与远程文件名保持一致
    filename = os.path.join(out_dir, url.split("/")[-1])

    try:
        wget.download(url, out=filename)
        print(f"\nDownloaded GIM data for {year}-{doy_str} to {filename}")
    except Exception as e:
        print(f"Failed to download GIM data for {year}-{doy_str}. Error: {e}")


def download_snx_data(year, doy, ac="COD", freq="daily", out_dir="."):
    """
    freq: "daily", or "weekly"
    ac: "COD", or "GFZ", or "MIT", or "NGS", or "IGS"
    
    ftp://igs.gnsswhu.cn/pub/gps/products/2246/IGS0OPSSNX_20230240000_01D_01D_SOL.SNX.gz #
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/SIO0OPSFIN_20223340000_01D_01D_SOL.SNX.gz
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/COD0OPSFIN_20223310000_01D_01D_SOL.SNX.gz
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/GFZ0OPSFIN_20223370000_01D_01D_SOL.SNX.gz
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/MIT0OPSFIN_20223310000_01D_01D_SOL.SNX.gz
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/NGS0OPSFIN_20223360000_01D_01D_SOL.SNX.gz
    ftp://igs.gnsswhu.cn/pub/gps/products/2238/SIO0OPSFIN_20223320000_01D_01D_SOL.SNX.gz
                                               IGS0OPSSNX_yyyyddd0000_07D_07D_SOL.SNX.gz
    
    """
    gpsw, gpsd = gnss_time.doy2gpsw(year, doy)
    base_url = "ftp://igs.gnsswhu.cn/pub/gps/products"
    doy_str = f"{doy:03d}"
    
    if gpsw >= 2238:
        url = 1
    else:
        url = f"{base_url}/{gpsw:04d}/{ac}{gpsw:04d}{int(gpsd):01d}.snx.Z"
    

def download_sp3_data(year, doy, out_dir="."):
    gpsw, gpsd = gnss_time.doy2gpsw(year, doy)
    base_url = "ftp://igs.gnsswhu.cn/pub/gps/products"
    doy_str = f"{doy:03d}"

    if datetime(year, 1, 1) + timedelta(days=doy - 1) <= datetime(2022, 11, 26):  # 2022年330天或之前
        url = f"{base_url}/{gpsw:04d}/igs{gpsw:04d}{int(gpsd):01d}.sp3.Z"
    else:
        url = f"{base_url}/{gpsw}/IGS0OPSFIN_{year}{doy_str}0000_01D_15M_ORB.SP3.gz"

    filename = os.path.join(out_dir, f"IGS0OPSFIN_{year}{doy_str}0000_01D_15M_ORB.SP3.gz")
    print(url)
    try:
        wget.download(url, out=filename)
        print(f"\nDownloaded SP3 data for {year}-{doy_str} to {filename}")
    except Exception as e:
        print(f"Failed to download SP3 data for {year}-{doy_str}. Error: {e}")


def download_clk_data(year, doy, out_dir="."):
    gpsw, gpsd = gnss_time.doy2gpsw(year, doy)
    base_url = "ftp://igs.gnsswhu.cn/pub/gps/products"
    doy_str = f"{doy:03d}"  # 使用 zfill 将 doy 格式化为三位数字

    if datetime(year, 1, 1) + timedelta(days=doy - 1) <= datetime(2022, 11, 26):  # 2022年330天或之前
        url = f"{base_url}/{gpsw:04d}/igs{gpsw:04d}{int(gpsd):01d}.clk.Z"
    else:
        url = f"{base_url}/{gpsw:04d}/IGS0OPSFIN_{year}{doy_str}0000_01D_05M_CLK.CLK.gz"

    filename = os.path.join(out_dir, f"IGS0OPSFIN_{year}{doy_str}0000_01D_05M_CLK.CLK.gz")

    try:
        wget.download(url, out=filename)
        print(f"\nDownloaded CLK data for {year}-{doy_str} to {filename}")
    except Exception as e:
        print(f"Failed to download CLK data for {year}-{doy_str}. Error: {e}")


def download_rnx2_data(year, doy, site, out_dir="."):
    yr = year-2000
    url=f"ftp://igs.gnsswhu.cn/pub/gps/data/daily/{year:04d}/{doy:03d}/{yr:02d}d/{site}{doy:03d}0.{yr:02d}d.Z"

    filename = os.path.join(out_dir, f"{site}{doy:03d}0.{yr:02d}d.Z")
    print(f"\ntrying to download {url}")
    try:
        wget.download(url, out=filename)
    except Exception as e:
        print(f"Failed to download rnx data for {year}-{doy}. Error: {e}")



def download_rnx3_data(year, doy, site, out_dir="."):
    yr = year-2000
    # url=f"ftp://igs.gnsswhu.cn/pub/gps/data/daily/{year:04d}/{doy:03d}/{yr:02d}d/{site}{doy:03d}0.{yr:02d}d.Z"
    url=f"ftp://igs.gnsswhu.cn/pub/gps/data/daily/{year:04d}/{doy:03d}/{yr:02d}d/{site}_R_{year:04d}{doy:03d}0000_01D_30S_MO.crx.gz"

    filename = os.path.join(out_dir, f"{site}_R_{year:04d}{doy:03d}0000_01D_30S_MO.crx.gz")
    print(f"\ntrying to download {url}")
    try:
        wget.download(url, out=filename)
    except Exception as e:
        print(f"Failed to download rnx data for {year}-{doy}. Error: {e}")


def download_code_dcb(year, month, dcbtype="code.dcb.p1p2", out_dir="."):
    # 确保输出目录存在
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # 计算二进制年
    yr = str(year % 100).zfill(2)
    
    # 构建文件名和URL
    if dcbtype.endswith("p1p2"):
        filename = f"P1P2{yr}{month:02d}_ALL.DCB.Z"
    elif (dcbtype.endswith("p1c1") or dcbtype.endswith("p2c2")):
        filename = f"P1C1{yr}{month:02d}_RINEX.DCB.Z"
        
    url = f"http://ftp.aiub.unibe.ch/CODE/{year}/{filename}"
    
    # 构建保存路径
    save_path = os.path.join(out_dir, filename)
    
    try:
        # 使用wget下载文件
        print(f"\ntrying to download {url}")
        wget.download(url, out=save_path)
        print(f"\n文件已成功下载到: {save_path}")
    except Exception as e:
        print(f"下载文件时出错: {e}")


def download_ilrs_daily_snx(year, doy, out_dir="."):
    # 将年积日转换为日期对象
    date = datetime.strptime(f"{year}-{doy:03d}", "%Y-%j")
    
    # 提取年份的后两位
    _, month, day = gnss_time.doy2ymd(year, doy)
    yr = year % 100
    day = int(day)
    # 判断日期以确定 ver 的值
    if date >= datetime(2017, 6, 13):
        ver = 170  # 2017 年 6 月 13 日及以后
    else:
        ver = 135  # 2017 年 6 月 12 日及以前
    
    # 构造 URL
    url = f"https://cddis.nasa.gov/archive/slr/products/pos+eop/{year:04d}/{yr:02d}{month:02d}{day:02d}/ilrsa.pos+eop.{yr:02d}{month:02d}{day:02d}.v{ver:03d}.snx.gz"
    
    
    # 构造输出文件名
    filename = f"ilrsa.pos+eop.{yr:02d}{month:02d}{day:02d}.v{ver:03d}.snx.gz"
    output_path = os.path.join(out_dir, filename)
    print(f"wget --auth-no-challenge -P {out_dir} {url}")


def download_ivs_daily_snx(year, doy, out_dir="."):
    _, month, day = gnss_time.doy2ymd(year, doy)
    # 将月份转换为 3 位简写（如 "JAN", "FEB"）
    month_abbr = datetime(year, month, 1).strftime("%b").upper()
    
    # 获取年份的后两位
    yr = year % 100
    
    # 构造 URL
    url = f"https://cddis.nasa.gov/archive/vlbi/ivsproducts/daily_sinex/ivs2020a/{yr:02d}{month_abbr}{int(day):02d}XE_ivs2020a.snx.gz"
    
    # 构造输出文件名
    filename = f"{yr:02d}{month_abbr}{int(day):02d}XE_ivs2020a.snx.gz"
    output_path = os.path.join(out_dir, filename)
    
    # 下载文件
    print(f"Downloading {url} to {output_path}...")
    try:
        wget.download(url, out=output_path)
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nFailed to download the file: {e}")

def download_igs_daily_snx(year, doy, out_dir="."):
    # 将 year 和 doy 转换为 GPS 周 (gpsw) 和 GPS 周内天 (dow)
    gpsw, dow = gnss_time.doy2gpsw(year, doy)
    
    # 构造日期对象，用于判断使用哪个 URL 模板
    date = datetime.strptime(f"{year}-{doy:03d}", "%Y-%j")  # 将年积日转换为日期
    
    # 判断日期是否在 2022年11月27日及以后
    if date >= datetime(2022, 11, 27):
        # 使用新模板
        url = f"ftp://igs.gnsswhu.cn/pub/gps/products/{gpsw:04d}/IGS0OPSSNX_{year:04d}{doy:03d}0000_01D_01D_SOL.SNX.gz"
        filename = f"IGS0OPSSNX_{year:04d}{doy:03d}0000_01D_01D_SOL.SNX.gz"
    else:
        # 使用旧模板
        yr = year % 100  # 取年份的后两位
        url = f"ftp://igs.gnsswhu.cn/pub/gps/products/{gpsw:04d}/igs{yr:02d}P{gpsw:04d}{int(dow):01d}.snx.Z"
        filename = f"igs{yr:02d}P{gpsw:04d}{int(dow):01d}.snx.Z"
    # 构造输出文件路径
    output_path = os.path.join(out_dir, filename)
    
    # 下载文件
    print(f"Downloading {url} to {output_path}...")
    try:
        wget.download(url, out=output_path)
        print("\nDownload complete.")
    except Exception as e:
        print(f"\nFailed to download the file: {e}")

def download_co1_l1b_podtec(year, doy, out_dir="."):
# 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # 构造完整的下载链接
    base_url = "https://data.cosmic.ucar.edu/gnss-ro/cosmic1/repro2021/level1b/"
    download_url = f"{base_url}{year:04d}/{doy:03d}/podTec_repro2021_{year:04d}_{doy:03d}.tar.gz"
    
    # 设置下载文件的路径
    output_file_path = os.path.join(out_dir, f"podTec_repro2021_{year:04d}_{doy:03d}.tar.gz")
    print(f"\ntrying to download {download_url}")
    try:
        # 使用 wget 库下载文件
        wget.download(download_url, out=output_file_path)
        print(f"文件已成功下载至: {output_file_path}")
    except Exception as e:
        print(f"下载失败: {e}")

def download_co2_l1b_podtc2(year, doy, out_dir="."):
    # 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # 构造完整的下载链接
    base_url = "https://data.cosmic.ucar.edu/gnss-ro/cosmic2/nrt/level1b/"
    download_url = f"{base_url}{year:04d}/{doy:03d}/podTc2_nrt_{year:04d}_{doy:03d}.tar.gz"
    
    # 设置下载文件的路径
    output_file_path = os.path.join(out_dir, f"podTc2_nrt_{year:04d}_{doy:03d}.tar.gz")
    print(f"\ntrying to download {download_url}")
    try:
        # 使用 wget 库下载文件
        wget.download(download_url, out=output_file_path)
        print(f"文件已成功下载至: {output_file_path}")
    except Exception as e:
        print(f"下载失败: {e}")
        

def download_co1_l2_ionprf(year, doy, out_dir="."):
# 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # 构造完整的下载链接
    base_url = "https://data.cosmic.ucar.edu/gnss-ro/cosmic1/repro2021/level2/"
    download_url = f"{base_url}{year:04d}/{doy:03d}/ionPrf_repro2021_{year:04d}_{doy:03d}.tar.gz"
    
    # 设置下载文件的路径  
    output_file_path = os.path.join(out_dir, f"ionPrf_repro2021_{year:04d}_{doy:03d}.tar.gz")
    print(f"\ntrying to download {download_url}")
    try:
        # 使用 wget 库下载文件
        wget.download(download_url, out=output_file_path)
        print(f"文件已成功下载至: {output_file_path}")
    except Exception as e:
        print(f"下载失败: {e}")

    
def download_co2_l2_ionprf(year, doy, out_dir="."):
    # 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    # 构造完整的下载链接
    base_url = "https://data.cosmic.ucar.edu/gnss-ro/cosmic2/provisional/spaceWeather/level2/"
    download_url = f"{base_url}{year:04d}/{doy:03d}/ionPrf_prov1_{year:04d}_{doy:03d}.tar.gz"
    # 设置下载文件的路径
    output_file_path = os.path.join(out_dir, f"ionPrf_prov1_{year:04d}_{doy:03d}.tar.gz")
    print(f"\ntrying to download {download_url}")
    
    try:
        # 使用 wget 库下载文件
        wget.download(download_url, out=output_file_path)
        print(f"文件已成功下载至: {output_file_path}")
    except Exception as e:
        print(f"下载失败: {e}")


def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="Download data for ppget script.")

    data_types= ['brdc', 'gim', 'sp3', 'clk', 'rnx2', 'rnx3', 
                 'igs.daily.snx', 'ilrs.daily.snx',
                 'code.dcb.p1p2', 'code.dcb.p1c1', 'code.dcb.p2c2', 
                 'co1.l2.ionprf', 'co1.l1b.podtec', 'co2.l1b.podtc2', 'co2.l2.ionprf']
    # 添加--data参数，允许的值为brdc, gim, sp3, clk
    parser.add_argument('--data', choices=data_types, help='Specify the type of data to download.')

    parser.add_argument("--site", dest="site", type=str, help="site name")
    # 添加--from参数，用于指定开始时间的年份和年积日
    parser.add_argument('--from', dest='start_date', type=parse_year_and_doy,
                        help='Specify the start date for data download. Format: year,doy')

    # 添加--to参数，用于指定结束时间的年份和年积日
    parser.add_argument('--to', dest='end_date', type=parse_year_and_doy,
                        help='Specify the end date for data download. Format: year,doy')

    # 添加--outdir参数，用于指定下载目录，默认为当前目录
    parser.add_argument('--outdir', default=".", help='Specify the local directory for downloaded files.')
    
    parser.add_argument("--proxy", default="", help="proxy server address")


    # 添加--help参数，显示脚本用法
    args = parser.parse_args()

    # 检查输出目录是否存在
    if not os.path.exists(args.outdir):
        print(f"Error: Directory '{args.outdir}' does not exist.")
        return

    if args.proxy:
        os.environ["http_proxy"] = args.proxy
        os.environ["https_proxy"] = args.proxy
    
    if args.data == "ilrs.daily.snx":
        print("\n# auth info is required to download file in CDDIS")
        print("# add auth info to .netrc file")
        print("# .netrc file")
        print("\n#    machine urs.earthdata.nasa.gov login <username> password <password>")
    
    if args.start_date and args.end_date:
        start_year, start_doy = args.start_date
        end_year, end_doy = args.end_date
        if args.data == "rnx2" or args.data == "rnx3":
            site = args.site
        start_date = datetime(start_year, 1, 1) + timedelta(days=start_doy - 1)
        end_date = datetime(end_year, 1, 1) + timedelta(days=end_doy - 1)
        last_month = 0
        current_date = start_date
        while current_date <= end_date:
            year, doy = current_date.year, current_date.timetuple().tm_yday

            if args.data == 'brdc':
                download_brdc_data(year, doy, out_dir=args.outdir)
            elif args.data == 'gim':
                download_gim_data(year, doy, out_dir=args.outdir)
            elif args.data == 'sp3':
                download_sp3_data(year, doy, out_dir=args.outdir)
            elif args.data == 'clk':
                download_clk_data(year, doy, out_dir=args.outdir)
            elif args.data=="rnx2":
                download_rnx2_data(year, doy, site, out_dir=args.outdir)
            elif args.data=="rnx3":
                download_rnx3_data(year, doy, site, out_dir=args.outdir)
            elif args.data=="igs.daily.snx":
                download_igs_daily_snx(year, doy, out_dir=args.outdir)
            # elif args.data=="ivs.daily.snx":
            #     download_ivs_daily_snx(year, doy, out_dir=args.outdir)
            elif args.data=="ilrs.daily.snx":
                download_ilrs_daily_snx(year, doy, out_dir=args.outdir)
            elif args.data=="code.dcb.p1p2" or args.data=="code.dcb.p1c1" or args.data=="code.dcb.p2c2":
                _, month, _ = gnss_time.doy2ymd(year, doy)
                if last_month == month: 
                    pass
                else:
                    download_code_dcb(year, month, dcbtype=args.data, out_dir=args.outdir)
                    last_month = month
            elif args.data=="co1.l2.ionprf":
                download_co1_l2_ionprf(year, doy, out_dir=args.outdir)
            elif args.data=='co1.l1b.podtec':
                download_co1_l1b_podtec(year, doy, out_dir=args.outdir)
            elif args.data=="co2.l1b.podtc2":
                download_co2_l1b_podtc2(year, doy, out_dir=args.outdir)
            elif args.data=="co2.l2.ionprf":
                download_co2_l2_ionprf(year, doy, out_dir=args.outdir)
            else:
                print(f"Error: Unsupported data type '{args.data}'")
                break

            current_date += timedelta(days=1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
