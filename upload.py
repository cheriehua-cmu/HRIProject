import paramiko

ROBOT_URL = "128.237.240.93"

c_path = "/home/aims/pepper-teleop/test.wav"
r_path = "/home/nao"

transport = paramiko.Transport((ROBOT_URL,22))
transport.connect(username="nao",password="nao")
sftp = paramiko.SFTPCLient.from_transport(transport)
sftp.put(c_path,r_path)

sftp.close()
transport.close()
