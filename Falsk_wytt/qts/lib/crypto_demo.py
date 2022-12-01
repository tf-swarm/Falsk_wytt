import base64
import os

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP, PKCS1_v1_5


class CryptoRsa:
    def __init__(self, password):
        self.rsa_public_key = None
        self.rsa_private_key = None
        self.password = password

    def create_rsa_key(self, path=None):
        """
        创建RSA密钥
        步骤说明：
        1、从 Crypto.PublicKey 包中导入 RSA，创建一个密码
        2、生成 1024/2048 位的 RSA 密钥
        3、调用 RSA 密钥实例的 exportKey 方法，传入密码、使用的 PKCS 标准以及加密方案这三个参数。
        4、将私钥写入磁盘的文件。
        5、使用方法链调用 publickey 和 exportKey 方法生成公钥，写入磁盘上的文件。

        """

        key = RSA.generate(1024)

        encrypted_key = key.exportKey(passphrase=self.password, pkcs=8, protection="scryptAndAES128-CBC")
        self.rsa_private_key = encrypted_key
        # print("---rsa_private_key---", self.rsa_private_key)
        with open(path + "rsa_private_key.pem", "wb") as f:
            f.write(encrypted_key)

        self.rsa_public_key = key.publickey().exportKey()
        # print("---rsa_public_key---", self.rsa_public_key)
        with open(path + "rsa_public_key.pem", "wb") as f:
            f.write(self.rsa_public_key)

    def rsa_encrypto(self, message, path=None,):
        # 加载公钥
        recipient_key = RSA.import_key(open(path + "rsa_public_key.pem").read())
        cipher_rsa = PKCS1_v1_5.new(recipient_key)
        msg = message.encode('utf8')
        en_data = cipher_rsa.encrypt(msg)

        # base64加密，方便网络传输
        bs = base64.b64encode(en_data).decode()
        return bs

    def rsa_decrypto(self, ciphertext, path=None):
        # 读取密钥
        private_key = RSA.import_key(open(path + "rsa_private_key.pem").read(), passphrase=self.password)
        cipher_rsa = PKCS1_v1_5.new(private_key)
        cipherbyte = base64.b64decode(ciphertext)  # base64解码
        data = cipher_rsa.decrypt(cipherbyte, None)
        return data.decode()


if __name__ == '__main__':
    path = os.path.dirname(__file__).split('qts')[0]
    cr = CryptoRsa(password='quant2021')
    # cr.create_rsa_key(path=path)
    res = cr.rsa_encrypto(message='039e93c4-5315c4bc-4fc1a6a5-8e83e', path=path)
    print("---res:", res)
    rsa_info = cr.rsa_decrypto(ciphertext=res, path=path)
    print("---rsa_info:", rsa_info)

