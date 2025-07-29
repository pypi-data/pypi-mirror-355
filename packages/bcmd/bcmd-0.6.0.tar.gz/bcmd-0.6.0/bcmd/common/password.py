import getpass
from typing import Any

from beni import bcache, bcrypto


@bcache.cache
async def getPypi() -> tuple[str, str]:
    content = 'QbuF2mV/lqovtF5dskZGD7qHknYbNuF2QseWRtWxLZTPrC/jL1tcxV8JEKaRjLsu46PxJZ7zepJwggnUTIWnEAoV5VtgP2/hbuzxxHha8817kR5c65H9fXm8eOal7DYXsUoGPQMnm59UWNXUKjmIaP4sn9nySFlRYqa8sEZSbYQ4N0NL35Dpj1e3wyQxJ+7h2jwKAz50Hh8G4yAM3/js9+NUe4ymts+UXcwsP3ADIBMkzjnFc0lEYg2d+fw0A74XWCvoZPoGqHZR/THUOVNAYxoGgDzP4SPIk1XsmtpxvfO/DpJd/Cg/0fB3MYagGKI1+m6Bxqhvd1I/lf0YbM5y4E4='
    data = _getData(content)
    return data['username'], data['password']


@bcache.cache
async def getQiniu() -> tuple[str, str]:
    content = '7xOuA0FPCndTWcWmWLbqklQTqLTAhuEw9CarRTBYhWQ/g8wPxktw6VAiu50TLv49D1L8oCVfGafsowYDZw/prF6NQwCluPcCMy5JfdC9sKauvuZa51Nsf6PTR1UIyU8ZLUSzH+Ec2Ufcz/yAZCrcAtn63zMHNu3tTAVcZNPL597lSHdSRkpmDR8CaoUh/raH/Q=='
    data = _getData(content)
    return data['ak'], data['sk']


def _getData(content: str) -> dict[str, Any]:
    index = content.find(' ')
    if index > -1:
        tips = f'请输入密码（{content[:index]}）：'
    else:
        tips = '请输入密码：'
    while True:
        try:
            pwd = getpass.getpass(tips)
            return bcrypto.decryptJson(content, pwd)
        except KeyboardInterrupt:
            raise Exception('操作取消')
        except BaseException:
            pass
