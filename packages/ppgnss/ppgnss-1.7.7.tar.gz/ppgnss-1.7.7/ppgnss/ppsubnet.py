import argparse
from collections import defaultdict
import math
import random
import os
import json
from heapq import heappush, heappop
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from typing import Dict, List, Tuple

# MAX_SUB_SITES = 90  # 每个子网最大站点数


def select_points(sites: Dict[str, Tuple[float, float, float]], num: int) -> List[str]:
    """
    从站点字典中选择指定数量的点，确保空间均匀分布
    
    :param sites: 站点字典，格式为 {站点名: (经度, 纬度, 高程)}
    :param num: 需要选择的站点数量
    :return: 选中的站点名称列表
    """
    # 边界条件处理
    if num <= 0 or not sites:
        return []
    
    total = len(sites)
    if num >= total:
        return list(sites.keys())
    
    # 将字典转换为可处理格式 (名称, 坐标)
    site_list = [(name, (lon, lat)) for name, (lon, lat, _) in sites.items()]
    
    # 初始化数据结构
    remaining = site_list.copy()
    selected_names = []
    
    # 随机选择第一个点
    first_idx = random.randint(0, len(remaining)-1)
    first_name, first_coord = remaining.pop(first_idx)
    selected_names.append(first_name)
    
    # 初始化距离数组 (到已选点的最小距离)
    distances = [_geo_distance(coord, first_coord) for _, coord in remaining]
    
    # 迭代选择剩余点
    while len(selected_names) < num:
        # 找到当前最远点
        max_idx = max(enumerate(distances), key=lambda x: x[1])[0]
        
        # 移动点到已选集合
        selected_name, selected_coord = remaining.pop(max_idx)
        selected_names.append(selected_name)
        del distances[max_idx]
        
        # 更新剩余点的最小距离
        for i in range(len(remaining)):
            new_dist = _geo_distance(remaining[i][1], selected_coord)
            distances[i] = min(distances[i], new_dist)
    
    return selected_names


def _geo_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """带纬度加权的简化距离计算"""
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    # 纬度差
    dlat = abs(lat1 - lat2)
    
    # 经度差 (修正环绕)
    dlon = abs(lon1 - lon2)
    dlon = min(dlon, 360 - dlon)
    
    # 纬度加权
    avg_lat = (lat1 + lat2) / 2
    adjusted_dlon = dlon * math.cos(math.radians(avg_lat))
    
    return math.sqrt(dlat**2 + adjusted_dlon**2)


def read_site_details(filename):
    """读取站点详细信息，返回字典：{站名: (经度, 纬度, 高程)}"""
    sites = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    lat = float(parts[1])
                    lon = float(parts[2])
                    elev = float(parts[3]) if len(parts) >= 4 else 0.0
                    sites[name] = (lon, lat, elev)
    return sites

def write_subnet_file(subnet_id, subnet, core_sites, site_details):
    """写入子网文件，连接点用*标记"""
    filename = f"subnet_{subnet_id}.txt"
    with open(filename, 'w') as f:
        f.write(f"# Subnet {subnet_id} ({len(subnet)} sites)\n")
        for site in subnet:
            prefix = "* " if site in core_sites else "  "
            lon, lat, elev = site_details[site]
            f.write(f"{prefix}{site} {lat:10.4f} {lon:10.4f} {elev:8.2f}\n")

def plot_subnets(subnets, site_details, core_sites):
    """使用Cartopy绘制多子图地理分布"""
    n = len(subnets)
    rows = int(np.sqrt(n))
    cols = int(np.ceil(n / rows))
    
    plt.figure(figsize=(cols*6, rows*5))
    plt.suptitle("GNSS Subnet Geographical Distribution", fontsize=14, y=0.95)
    
    for idx, subnet in enumerate(subnets, 1):
        ax = plt.subplot(rows, cols, idx, projection=ccrs.PlateCarree())
        
        # 计算当前子网的经纬度范围
        lons = [site_details[s][0] for s in subnet]
        lats = [site_details[s][1] for s in subnet]
        pad = 2  # 经纬度扩展范围
        # ax.set_extent([min(lons)-pad, max(lons)+pad, 
        #               min(lats)-pad, max(lats)+pad], crs=ccrs.PlateCarree())
        ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())
        
        # 添加地理要素
        ax.add_feature(cfeature.LAND, zorder=0)
        ax.add_feature(cfeature.OCEAN, zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=2)
        ax.add_feature(cfeature.BORDERS, linestyle=':', zorder=2)
        ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, zorder=1)
        
        # 绘制站点
        for site in subnet:
            lon, lat, _ = site_details[site]
            if site in core_sites:
                ax.plot(lon, lat, '^', color='red', markersize=8,
                       transform=ccrs.PlateCarree(), label='Core Site' if idx==1 else None)
            else:
                ax.plot(lon, lat, 'o', color='blue', markersize=6,
                       transform=ccrs.PlateCarree(), label='Normal Site' if idx==1 else None)
        
        ax.set_title(f"Subnet {idx} ({len(subnet)} sites)")

    # 添加图例
    handles, labels = ax.get_legend_handles_labels()
    plt.figlegend(handles, ['Core Site', 'Normal Site'], 
                 loc='lower center', ncol=2, fontsize=10)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('subnets_geo_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def write_statistics(subnets, core_sites, site_details):
    """生成统计结果文件"""
    total_subnets = len(subnets)
    core_usage = {site:0 for site in core_sites}
    
    # 统计核心站点使用次数
    for subnet in subnets:
        for site in subnet:
            if site in core_usage:
                core_usage[site] += 1
    
    with open('subnet_statistics.txt', 'w') as f:
        # 全局统计
        f.write("GNSS Subnet Statistical Report\n")
        f.write("="*50 + "\n")
        f.write(f"Total Subnets: {total_subnets}\n")
        f.write(f"Total Core Sites: {len(core_sites)}\n")
        f.write(f"Average Core Reuse: {sum(core_usage.values())/len(core_sites):.2f}\n\n")
        
        # 子网详细统计
        for idx, subnet in enumerate(subnets, 1):
            core_in_subnet = [s for s in subnet if s in core_sites]
            normal_in_subnet = [s for s in subnet if s not in core_sites]
            
            f.write(f"Subnet {idx} ({len(subnet)} sites)\n")
            f.write("-"*50 + "\n")
            f.write(f"Core Sites ({len(core_in_subnet)}): {', '.join(core_in_subnet)}\n")
            f.write(f"Normal Sites ({len(normal_in_subnet)}): {', '.join(normal_in_subnet)}\n")
            
            # 计算指标
            reuse_rates = [core_usage[s]/total_subnets for s in core_in_subnet]
            avg_reuse = sum(reuse_rates)/len(reuse_rates) if reuse_rates else 0
            core_ratio = len(core_in_subnet)/len(subnet)
            
            f.write(f"Average Core Reuse: {avg_reuse:.2%}\n")
            f.write(f"Core Ratio in Subnet: {core_ratio:.2%}\n\n")
        
        # 核心站点使用详情
        f.write("\nCore Site Usage Details:\n")
        f.write("-"*50 + "\n")
        for site, count in sorted(core_usage.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{site}: Used in {count}/{total_subnets} subnets ({count/total_subnets:.2%})\n")

def main():
    conf_file = "conf.json"
    conf = defaultdict()
    if os.path.isfile(conf_file):
        with open("conf.json", "r") as fread:
            conf = json.load(fread)
    else:
        parser = argparse.ArgumentParser(description="GNSS站点子网划分工具")
        parser.add_argument('--stations', dest='sitestbl', default='stations.txt',
                        help='站点列表文件（默认：stations.txt）')
        parser.add_argument('--coresites', dest='coresites', default='coresites.txt',
                        help='核心站点文件（默认：coresites.txt）')
        parser.add_argument('--repeat', type=float, default=0.6,
                        help='连接点重复度（默认：0.6，范围：0.5-1.0）')
        parser.add_argument('--core_ratio', type=float, default=0.2,
                        help='子网连接点比例（默认：0.2，范围：0.05-0.3）')
        args = parser.parse_args()
        if args.sitestbl:
            conf["sitestbl"] = args.sitestbl
        if args.coresites:
            conf["coresites"] = args.coresites
        if args.repeat:
            conf["repeat"] = args.repeat
        if args.core_ratio:
            conf["core_ratio"] = args.core_ratio
            # -------------------- 输入验证 --------------------

    print(conf)

    if not os.path.exists(conf["sitestbl"]):
        print(f"错误：站点文件 {conf["sitestbl"]} 不存在")
        return
    
    site_details = read_site_details(conf["sitestbl"])
    if not site_details:
        print("错误：站点文件中无有效数据")
        return
    all_sites = list(site_details.keys())

    # 处理核心站点
    if conf["coresites"] and os.path.exists(conf["coresites"]) :
        cores = []
        with open(conf["coresites"], 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    cores.extend(line.strip().split())
        cores = list(set(cores))
        invalid = [s for s in cores if s not in all_sites]
        if invalid:
            print(f"错误：无效核心站点 {invalid}")
            return
    else:
        core_num = min(math.ceil(len(all_sites)/5), len(all_sites))
        # cores = random.sample(all_sites, core_num)
        # print(all_sites)
        cores = select_points(site_details, core_num)

    # -------------------- 参数调整 --------------------
    q = max(0.05, min(conf["core_ratio"], 0.3))
    p = max(0.5, min(conf["repeat"], 1.0))
    
    if "subnets_num" not in conf:
        nets_num = None
    else:
        nets_num = conf["subnets_num"]
    
    if nets_num is None:
        max_sites_in_net = 90
    else:
        max_sites_in_net = len(all_sites)/(nets_num - int(math.ceil((nets_num-1)*q)))
    
    # 动态计算连接点参数
    while True:
        k = int(max_sites_in_net * q)
        if k < 1:
            print("错误：无法满足最小连接点数量")
            return
        K = math.ceil(k / p) if p != 0 else 0
        if len(cores) >= K:
            break
        q *= 0.9
        if q < 0.05:
            print(f"错误：核心站点不足，需要{K}个，仅有{len(cores)}个")
            return

    # -------------------- 子网划分 --------------------
    # 选择连接点
    L = random.sample(cores, K)
    U = [s for s in all_sites if s not in L]

    # 分配非连接点
    s_noncore = max_sites_in_net - k
    
    # 计算子网站点数
    if nets_num is None:
        nets_num = math.ceil(len(U) / s_noncore)  # 理论子网数

    base = len(U) // nets_num
    remainder = len(U) % nets_num
    subnet_sizes = [base + 1] * remainder + [base] * (nets_num - remainder)

    random.shuffle(U)
    subnets_noncore = []
    start = 0
    for size in subnet_sizes:
        end = start + size
        subnets_noncore.append(U[start:end])
        start = end

    # 连接点分配
    usage = {site: 0 for site in L}
    heap = [(0, site) for site in L]
    max_usage = math.ceil(p * nets_num)
    subnets = []

    for noncore in subnets_noncore:
        selected = []
        temp_heap = []
        while len(selected) < k and heap:
            cnt, site = heappop(heap)
            if usage[site] < max_usage:
                selected.append(site)
                usage[site] += 1
                heappush(temp_heap, (cnt + 1, site))
            else:
                heappush(temp_heap, (cnt, site))
        heap += temp_heap
        
        if len(selected) < k:
            print("错误：连接点不足，请调整参数")
            return
        
        subnet = noncore + selected
        # if len(subnet) > MAX_SUB_SITES:
        #     print("错误：子网容量超标")
        #     return
        subnets.append(subnet)

    # -------------------- 输出结果 --------------------
    all_core_sites = set(L)
    
    # 写入子网文件
    for idx, subnet in enumerate(subnets, 1):
        write_subnet_file(idx, subnet, all_core_sites, site_details)
    
    # 绘制地理分布图
    plot_subnets(subnets, site_details, all_core_sites)
    
    # 生成统计报告
    write_statistics(subnets, all_core_sites, site_details)
    
    print("处理完成！输出文件：")
    print(f"- subnet_*.txt：各子网站点列表")
    print(f"- subnets_geo_distribution.png：地理分布图")
    print(f"- subnet_statistics.txt：统计报告")

if __name__ == "__main__":
    main()