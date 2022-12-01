import configparser


__all__ = ['truncation', 'truncation_list', 'get_ini', 'set_ini']

def truncation( num, precision):
		'''
		对浮点型截断小数点位数
		param: 浮点数，保留的小数点位数
		return: 
		'''
		if precision == 0:
			return int(num)
		else:
			decimal = 10**precision
			data = int(num*decimal)
			return data/decimal

#对整个list进行截断
def truncation_list( nArr,precision):
	'''
	对整个list里面的数的浮点型进行保留小数点操作
	param: list，保留的小数点位数
	'''
	if len(nArr) != 0:
		for i in range(len(nArr)):
			if precision == 0:
				nArr[i] = int(nArr[i])
			else:
				nArr[i] = truncation(nArr[i],precision)
	return nArr 


def get_ini(path, section, key):
	try:
		config = configparser.ConfigParser()
		config.read(path)
		return config.get(section, key)
	except Exception as e:
		print("e:",e)
		return -1

def set_ini(path, section, keys, values):
	try:
		config = configparser.ConfigParser()
		config.read(path)
		cfgfile = open(path, 'w')
		config.set(section, keys, values)
		config.write(cfgfile)
		cfgfile.close()
	except Exception as e:
		print(e)
		return -1