# import pyotp
from PepperPepper.environment import pyotp

def get2fa(key='DFTJUMMSOSCFLLPLPYKNUHCR2PL7653G'):
    totp = pyotp.TOTP(key)
    code = totp.now()
    return code


if __name__ == '__main__':
    code = get2fa()
    print(code)




