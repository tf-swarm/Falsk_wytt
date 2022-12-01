#import itchat
import dingtalkchatbot.chatbot as cb 

# def wx_login():
# 	'''
# 	登陆网页版微信
# 	'''
# 	try:
# 		itchat.auto_login(hotReload=True)
# 		return 0
# 	except Exception as e:
# 		print(e)
# 		return -1

# def wx_sendmsg(friend,msg):
# 	'''
# 	发送微信信息
# 	param: 好友名称 消息
# 	'''
# 	try:
# 		userfinfo = itchat.search_friends(friend)
# 		print(userfinfo)
# 		userid = userfinfo[0]['UserName']
# 		itchat.send(msg, userid)
# 	except Exception as e:
# 		print(e)
# 		return -1
	

def dingding_sendmsg(msg):
	'''
	发送钉钉消息
	'''
	#SEC2e6c06c079b3b5a45b51e7be927638195a1c1b44def39c07e8482d75dc4aeeb4
	try:
		webhook = 'https://oapi.dingtalk.com/robot/send?access_token=5cb1c2c95fb995ed23257c5b190d1790f3a3b101983894dde8c2c24d21790383'
		secret = 'SECc81a6ff32a5b27f43914b677f50f0a4107e29c0f6a84052d27f4b80a0d8da3d7'

		xiaoding = cb.DingtalkChatbot(webhook, secret = secret)

		res = xiaoding.send_text(msg=msg)

	except Exception as e:
		print(e)


if __name__ == '__main__':
	dingding_sendmsg('机器人测试')