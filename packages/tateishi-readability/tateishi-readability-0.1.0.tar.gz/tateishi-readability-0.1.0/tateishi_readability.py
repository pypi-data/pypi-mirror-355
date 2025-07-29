from divide_char_type import divide_char_type
import re

def tateishi_readability(text):
	data = divide_char_type(text)

	#pa:アルファベット連の連全体に対する頻度（％）
	#ph:ひらがな連の連全体に対する頻度（％）
	#pc:漢字連の連全体に対する頻度（％）
	#pk:カタカナ連の連全体に対する頻度（％）
	#ls:文の平均長さ（文字）
	#la:アルファベット連の平均長さ（文字）
	#lh:ひらがな連の平均長さ（文字）
	#lc:漢字連の平均長さ（文字）
	#lk:カタカナ連の平均長さ（文字）
	#cp:句点あたり読点の数

	ren_total = len(data[2]+data[3]+data[4]+data[5]+data[6])
	pa = len(data[5]+data[6])/ren_total
	ph = len(data[2])/ren_total
	pc = len(data[4])/ren_total
	pk = len(data[3])/ren_total
	ls = sum([len(x) for x in (data[2]+data[3]+data[4]+data[5]+data[6])])/ren_total
	la = sum([len(x) for x in (data[5]+data[6])])/(len(data[5]+data[6]) or 1)
	lh = sum([len(x) for x in data[2]])/(len(data[2]) or 1)
	lc = sum([len(x) for x in data[4]])/(len(data[4]) or 1)
	lk = sum([len(x) for x in data[3]])/(len(data[3]) or 1)
	
	re_point = re.compile("[.．…。!?！？]")
	re_comma = re.compile("[,，、]")
	point_total = len([x for x in data[7] if re.search(re_point, x)]) or 1
	comma_total = len([x for x in data[7] if re.search(re_comma, x)])
	cp = comma_total/point_total

	result = 0.05*pa+0.25*ph-0.19*pc-0.61*pk-1.34*ls-1.35*la+7.52*lh-22.1*lc-5.3*lk-3.87*cp+109.1

	return result


def tateishi_readability2(text):
	data = divide_char_type(text)

	#ls:文の平均長さ（文字）
	#la:アルファベット連の平均長さ（文字）
	#lh:ひらがな連の平均長さ（文字）
	#lc:漢字連の平均長さ（文字）
	#lk:カタカナ連の平均長さ（文字）
	#cp:句点あたり読点の数

	ren_total = len(data[2]+data[3]+data[4]+data[5]+data[6])
	ls = sum([len(x) for x in (data[2]+data[3]+data[4]+data[5]+data[6])])/ren_total
	la = sum([len(x) for x in (data[5]+data[6])])/(len(data[5]+data[6]) or 1)
	lh = sum([len(x) for x in data[2]])/(len(data[2]) or 1)
	lc = sum([len(x) for x in data[4]])/(len(data[4]) or 1)
	lk = sum([len(x) for x in data[3]])/(len(data[3]) or 1)
	
	re_point = re.compile("[.．…。!?！？]")
	re_comma = re.compile("[,，、]")
	point_total = len([x for x in data[7] if re.search(re_point, x)]) or 1
	comma_total = len([x for x in data[7] if re.search(re_comma, x)])
	cp = comma_total/point_total

	result = -0.12*ls-1.37*la+7.4*lh-23.18*lc-5.4*lk-4.67*cp+115.79

	return result

