import os
from pathlib import Path
from typing import Final

import typer
from beni import bcolor, bfile, bpath, brun, btask
from beni.bfunc import syncCall

from ..common import password

app: Final = btask.newSubApp('lib 工具')


@app.command()
@syncCall
async def update_version(
    path: Path = typer.Argument(Path.cwd(), help='workspace 路径'),
    isNotCommit: bool = typer.Option(False, '--no-commit', '-d', help='是否提交git'),
):
    '修改 pyproject.toml 版本号'
    file = path / 'pyproject.toml'
    btask.assertTrue(file.is_file(), '文件不存在', file)
    data = await bfile.readToml(file)
    version = data['project']['version']
    versionList = [int(x) for x in version.split('.')]
    versionList[-1] += 1
    newVersion = '.'.join([str(x) for x in versionList])
    content = await bfile.readText(file)
    if f"version = '{version}'" in content:
        content = content.replace(f"version = '{version}'", f"version = '{newVersion}'")
    elif f'version = "{version}"' in content:
        content = content.replace(f'version = "{version}"', f'version = "{newVersion}"')
    else:
        raise Exception('版本号修改失败，先检查文件中定义的版本号格式是否正常')
    await bfile.writeText(file, content)
    bcolor.printCyan(newVersion)
    if not isNotCommit:
        msg = f'更新版本号 {newVersion}'
        os.system(
            rf'TortoiseGitProc.exe /command:commit /path:{file} /logmsg:"{msg}"'
        )
    bcolor.printGreen('OK')


@app.command()
@syncCall
async def build(
    path: Path = typer.Argument(Path.cwd(), help='workspace 路径'),
    isKeepBuildFiles: bool = typer.Option(False, '--keep-build-files', '-k', help='是否保留构建文件'),
):
    '发布项目'
    user, pwd = await password.getPypi()
    bpath.remove(path / 'dist')
    bpath.remove(
        *list(path.glob('*.egg-info'))
    )
    with bpath.changePath(path):
        await brun.run(f'uv build')
        await brun.run(f'uv publish -u {user} -p {pwd}')
