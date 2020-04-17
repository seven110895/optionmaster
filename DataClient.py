import paramiko


class DataClient:
    def __init__(self, hostname, port, username, password):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.client.connect(hostname=self.hostname, port=self.port, username=self.username, password=self.password)

    def getfiles(self,date,currency):
        cmd = 'ls '+ '/home/ec2-user/deribit/' + str(date) + '/' + currency + '*'
        stdin, stdout, stderr = self.client.exec_command(cmd)
        result = stdout.read().decode('utf-8')
        return result.split('\n')

    def getfile(self,file):
        cmd = 'cat ' + file
        stdin, stdout, stderr = self.client.exec_command(cmd)
        dataFile = stdout.read().decode('utf-8')
        # print(dataFile)
        return dataFile
client = DataClient('3.17.63.79', 22, 'ec2-user', 'Waa9b25xyk')
client.connect()
