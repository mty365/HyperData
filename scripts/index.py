import OScommon
from datetime import datetime, timedelta
import json
import os
import config
import time
from sys import platform

weekday_number = datetime.now().date().weekday()
weeks = []

for i in range(0 - weekday_number , 7):
	day = datetime.now().date() + timedelta(days=i)
	weeks.append(day.strftime("%Y-%m-%d"))
updates = {
	"recent":{
		"time": "",
		"developing": "no",
		"roms": []
	}
}
updates["recent"]['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for device in OScommon.order:
	devdata = OScommon.localData(device)
	code = devdata['device']
	name = {
		"zh": devdata['name']['zh'],
		"en": devdata['name']['en']
	}
	roms = ""
	for num in range(len(devdata['branches'])):
		tag = devdata['branches'][num]['idtag']
		branch = devdata["branches"][num]["branchtag"]
		if branch == 'X' or branch == 'D' or "Enterprise" in devdata["branches"][num]["name"]["en"] or "EP" in devdata["branches"][num]["name"]["en"] or "Demo" in devdata["branches"][num]["name"]["en"]:
			i = 0
		else:
			for rom in devdata['branches'][num]['roms']:
				if devdata['branches'][num]['roms'][rom]['release'] in weeks:
					if devdata['branches'][num]['roms'][rom]['os'] in roms:
						i = 0
					else:
						roms = roms + "; " + devdata['branches'][num]['roms'][rom]['os']
	if roms[2:] == "":
		i = 0
	elif roms[2:] in updates.__str__():
		i = 0
	else:
		json_str = '{"code": "'+code+'",''"name": '+json.dumps(name)+',"rom": "'+roms[2:]+'"}'
		updates["recent"]['roms'].append(json.loads(json_str))

with open('public/data/index.json', 'w', encoding='utf-8') as f:
	json.dump(updates, f, ensure_ascii=False, indent=2)
f.close()
errors = []
for device in OScommon.currentStable:
	if device in OScommon.unreleased:
		i = 0
	else:
		devdata = OScommon.localData(device)
		checker = OScommon.entryChecker(devdata,device)
		devlength = len(devdata["branches"])
		for num in range(devlength): 	
			branch = devdata["branches"][num]["branchtag"]
			if branch == 'X' or branch == 'D' or "Enterprise" in devdata["branches"][num]["name"]["en"] or "EP" in devdata["branches"][num]["name"]["en"]:
				i = 0
			else:
				roms = [list(devdata['branches'][num]["roms"].keys())][0]
				for i in range(len(roms)-1):
					if OScommon.compare(roms[i],roms[i+1]) == False:
						errors.append(1)
						print(device,roms[i],roms[i+1],"版本顺序有误，请核实")
					else:
						i = 0
		if checker ==0:
			i = 0
		else:
			errors.append(1)

if 1 in list(set(errors)):
	print("数据有误，请核实后提交git")
else:
	# 新增功能：遍历 devices.json，从各设备文件中读取 supports 和 android 字段并更新
	print("开始更新 devices.json 中的 supports 和 android 字段...")
	
	# 读取 devices.json
	devices_json_path = 'public/data/devices.json'
	with open(devices_json_path, 'r', encoding='utf-8') as f:
		devices_data = json.load(f)
	
	updated_count = 0
	# 遍历所有品牌
	for brand_key in devices_data:
		brand_info = devices_data[brand_key]
		if 'devices' not in brand_info:
			continue
		
		# 遍历该品牌下的所有设备
		for device_idx, device_info in enumerate(brand_info['devices']):
			code = device_info.get('code')
			if not code:
				continue
			
			# 构建设备文件路径
			device_file_path = f'public/data/devices/{code}.json'
			
			# 检查设备文件是否存在
			if not os.path.exists(device_file_path):
				print(f"  ⚠ 警告: 设备文件不存在 - {device_file_path}")
				continue
			
			try:
				# 读取设备文件
				with open(device_file_path, 'r', encoding='utf-8') as f:
					device_data = json.load(f)
				
				# 提取 supports 和 android 字段
				supports = device_data.get('suppports', [])
				android = device_data.get('android', [])
				
				# 更新到 devices.json 中
				if supports or android:
					devices_data[brand_key]['devices'][device_idx]['supports'] = supports
					devices_data[brand_key]['devices'][device_idx]['android'] = android
					updated_count += 1
					
			except Exception as e:
				print(f"  ✗ 错误: 处理 {code} 时出错 - {str(e)}")
				continue
	
	# 保存更新后的 devices.json
	with open(devices_json_path, 'w', encoding='utf-8') as f:
		json.dump(devices_data, f, ensure_ascii=False, indent='\t')
	
	print(f"✓ 完成！共更新了 {updated_count} 个设备的 supports 和 android 字段")
	print()
	
	os.system(f"cd public/data && git add . && git commit -m {updates['recent']['time'].replace(" " , "-")} && git push origin main")
	time.sleep(8)
	os.system(f"curl -X POST \"{config.deploy_url}\"")
	if platform == "win32":
		os.system(f"cls")
	else:
		os.system(f"clear")
	print("数据提交成功")
	print("网站已更新")
